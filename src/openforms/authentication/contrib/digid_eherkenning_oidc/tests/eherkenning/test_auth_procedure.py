from unittest.mock import patch

from django.test import TestCase, override_settings, tag
from django.urls import reverse

import requests_mock
from furl import furl
from rest_framework import status

from digid_eherkenning_oidc_generics.models import OpenIDConnectEHerkenningConfig
from openforms.accounts.tests.factories import StaffUserFactory
from openforms.authentication.tests.utils import get_start_form_url, get_start_url
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory

default_config = OpenIDConnectEHerkenningConfig(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "kvk"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class eHerkenningOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backends=["eherkenning_oidc"],
        )

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
            return_value=default_config,
        )
        self.mock_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.requests_mocker = requests_mock.Mocker()
        self.addCleanup(self.requests_mocker.stop)
        self.requests_mocker.start()

    def test_redirect_to_eherkenning_oidc(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        form_url = get_start_form_url(self.form)
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")

        response = self.client.get(start_url)

        with self.subTest("Sends user to IdP"):
            self.assertEqual(status.HTTP_302_FOUND, response.status_code)

            redirect_target = furl(response.url)  # type: ignore
            query_params = redirect_target.query.params

            self.assertEqual(redirect_target.host, "provider.com")
            self.assertEqual(
                redirect_target.path,
                "/auth/realms/master/protocol/openid-connect/auth",
            )
            self.assertEqual(query_params["scope"], "openid kvk")
            self.assertEqual(query_params["client_id"], "testclient")
            self.assertEqual(
                query_params["redirect_uri"],
                f"http://testserver{reverse('eherkenning_oidc:oidc_authentication_callback')}",
            )

        with self.subTest("Return state setup"):
            oidc_login_next = furl(self.client.session["oidc_login_next"])
            query_params = oidc_login_next.query.params

            self.assertEqual(
                oidc_login_next.path,
                reverse(
                    "authentication:return",
                    kwargs={"slug": self.form.slug, "plugin_id": "eherkenning_oidc"},
                ),
            )
            self.assertEqual(query_params["next"], form_url)

    def test_redirect_to_eherkenning_oidc_internal_server_error(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=500,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")

        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        assert self.requests_mocker.last_request is not None
        self.assertEqual(
            self.requests_mocker.last_request.url,
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
        )
        parsed = furl(response.url)  # type: ignore

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, f"/{self.form.slug}/")
        query_params = parsed.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "eherkenning_oidc"
        )

    def test_redirect_to_eherkenning_oidc_callback_error(self):
        # set up session/state
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")
        response = self.client.get(start_url)
        assert response.status_code == 302
        assert response.url.startswith("http://provider.com")  # type: ignore

        with patch(
            "openforms.authentication.contrib.digid_eherkenning_oidc.backends"
            ".OIDCAuthenticationEHerkenningBackend.verify_claims",
            return_value=False,
        ):
            response = self.client.get(reverse("eherkenning_oidc:callback"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.path, f"/{self.form.slug}/")
        self.assertEqual(query_params["_start"], "1")
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "eherkenning_oidc"
        )

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[])
    def test_redirect_to_disallowed_domain(self):
        start_url = get_start_url(
            self.form, plugin_id="eherkenning_oidc", host="http://example.com"
        )

        response = self.client.get(start_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://example.com"]
    )
    def test_redirect_to_allowed_domain(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        form_url = get_start_form_url(self.form, host="http://example.com")
        start_url = get_start_url(
            self.form, plugin_id="eherkenning_oidc", host="http://example.com"
        )

        response = self.client.get(start_url)

        with self.subTest("Sends user to IdP"):
            self.assertEqual(status.HTTP_302_FOUND, response.status_code)
            self.assertTrue(response.url.startswith("http://provider.com/"))  # type: ignore

        with self.subTest("Return state setup"):
            oidc_login_next = furl(self.client.session["oidc_login_next"])
            expected_next = reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "eherkenning_oidc"},
            )
            self.assertEqual(oidc_login_next.path, expected_next)
            query_params = oidc_login_next.query.params
            self.assertEqual(query_params["next"], form_url)

    def test_redirect_with_keycloak_identity_provider_hint(self):
        self.mock_config.return_value.oidc_keycloak_idp_hint = "oidc-eHerkenning"
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")

        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        parsed = furl(response.url)  # type: ignore
        query_params = parsed.query.params
        self.assertEqual(query_params["kc_idp_hint"], "oidc-eHerkenning")

    @tag("gh-3656", "gh-3692")
    # This is an example of a specific provider. It may differ when a different provider is used.
    # According to https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
    # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the error we expect from OIDC
    def test_redirect_to_form_when_login_cancelled_by_anonymous_user(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")
        response = self.client.get(start_url)
        assert response.status_code == 302
        assert response.url.startswith("http://provider.com")  # type: ignore

        response = self.client.get(
            reverse("eherkenning_oidc:callback"),
            {
                "error": "access_denied",
                "error_description": "The user cancelled",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)  # type: ignore
        query_params = parsed.query.params

        self.assertEqual(query_params["_eherkenning-message"], "login-cancelled")
        self.assertIsNone(query_params.get(BACKEND_OUTAGE_RESPONSE_PARAMETER))

    @tag("gh-3656", "gh-3692")
    def test_redirect_to_form_when_login_cancelled_by_authenticated_user(self):
        # set up session/state
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        user = StaffUserFactory.create()
        start_url = get_start_url(self.form, plugin_id="eherkenning_oidc")
        self.client.force_login(user=user)
        response = self.client.get(start_url)
        assert response.status_code == 302
        assert response.url.startswith("http://provider.com")  # type: ignore

        response = self.client.get(
            reverse("eherkenning_oidc:callback"),
            {"error": "access_denied", "error_description": "The user cancelled"},
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(query_params["_eherkenning-message"], "login-cancelled")
        self.assertIsNone(query_params.get(BACKEND_OUTAGE_RESPONSE_PARAMETER))
