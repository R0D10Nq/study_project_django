import Base from 'js_core/base-controller';

export default class ModalQuiz extends Base {


    _init() {

        return true;
    }

    /**
     * Бинд событий
     *
     * @returns {boolean}
     */
    _bind() {

        let button = $('[data-js-popup="modal-quiz"]'),
            textSlider = $('[data-js-quiz="text"]');

        button.on('click', function(){

            textSlider.slick('refresh');

        });

        return true;
    }
}
