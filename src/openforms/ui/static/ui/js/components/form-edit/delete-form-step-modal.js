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


const DeleteFormStepModal = ({formUUID, formStepUUID, isOpen, handleCloseFunction}) => {

    return (
        <Modal
            isOpen={isOpen}
            style={customModalStyles}
        >
            <h1 className="title">Delete Form Step: {formStepUUID}</h1>
            <button onClick={_ => handleCloseFunction()}>Close</button>
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
