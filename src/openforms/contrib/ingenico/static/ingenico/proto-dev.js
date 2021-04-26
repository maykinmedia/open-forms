/*
    entrypoint for quick development
*/
import 'regenerator-runtime/runtime.js';

// import {connectsdk} from 'connect-sdk-client-js/dist/connectsdk';


class IngenicoService {

    constructor(apiURL) {
        this.apiURL = apiURL;
        this._session = null;
    }

    async apiRequest(path, method = 'get', data = null) {
        method = method.toUpperCase();
        // TODO get params
        const res = await fetch(this.apiURL + path, {
            method: method,
            cache: 'no-cache',
            // cors: 'cors',
            // credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: (data ? JSON.stringify(data) : undefined)
        });
        return res;
    }

    async initiateCheckout(someIdentifyingParameter) {
        const data = {
            'step': someIdentifyingParameter,
            'return_url': window.location.href,
        };
        console.log(data);
        const res = await this.apiRequest('checkout', 'post', data);
        if (res.status !== 200) {
            throw Error('bad status: ' + res.status + ' ' + res.statusText);
        } else {
            const info = await res.json();
            console.log(info);
            return this.getRedirect(info['redirectUrl']);
        }
    }

    getRedirect(url) {
        return () => {
            console.log('redirecting to :' + url);
            window.location = url;
        };
    }

}


async function main() {
    console.log('main');
    let apiURL = 'http://localhost:8000/backends/ingenico/dev/api/';
    let service = new IngenicoService(apiURL);

    document.getElementById('button-checkout').addEventListener('click', async (e) => {
        let redirect = await service.initiateCheckout('xyz');
        console.log(redirect);
        redirect();
    });
}

main();
