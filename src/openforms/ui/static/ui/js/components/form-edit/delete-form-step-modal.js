import React from "react";
import Modal from "react-modal";
import PropTypes from 'prop-types';
import {destroy} from './api';


const customModalStyles = {
  content : {
    top                   : '50%',
    left                  : '50%',
    right                 : 'auto',
    bottom                : 'auto',
    marginRight           : '-50%',
    transform             : 'translate(-50%, -50%)'
  }
};


const DeleteFormStepModal = ({formUUID, formStepUUID, formStepNumber, isOpen, handleCloseFunction}) => {

    // TODO Need to update the states in form-edit so the deleted step is no longer shown on the frontend

    const deleteFormStep = () => {
        destroy(`/api/v1/forms/${formUUID}/steps/${formStepUUID}`).then(e => {
            console.log(e);
        });
    };

    return (
        <Modal
            isOpen={isOpen}
            style={customModalStyles}
        >
            <h1 className="title">Delete Form Step {formStepNumber}</h1>
            <button onClick={_ => {
                // TODO Only do this if the step was saved on the backend
                //   Maybe make formStepUUID optional and only do function call if formStepUUID exists
                //   since a form step only created in the front end will not have a uuid
                deleteFormStep();
                handleCloseFunction();
            }}>
                Delete
            </button>
            <button onClick={_ => {
                handleCloseFunction();
            }}>
                Cancel
            </button>
        </Modal>
    );
};

DeleteFormStepModal.propTypes = {
    formUUID: PropTypes.string.isRequired,
    formStepUUID: PropTypes.string.isRequired,
    isOpen: PropTypes.bool.isRequired,
    handleCloseFunction: PropTypes.func.isRequired
};

export default DeleteFormStepModal;
