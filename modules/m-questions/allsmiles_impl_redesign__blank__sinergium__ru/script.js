import Base  from 'js_core/base-controller';

export default class Question extends Base {

    /**
     * Инициализация
     *
     * @returns {boolean}
     */
    _init() {

        return true;
    }

    /**
     * Бинд событий
     *
     * @returns {boolean}
     */
    _bind() {

        let questionsFormWrapper = document.querySelector('.questions__form-wrapper');

        if ( questionsFormWrapper ) {

            let inputName = questionsFormWrapper.querySelector('.form__group_name'),
                inputText = questionsFormWrapper.querySelector('.form__group_text'),
                inputPhone = questionsFormWrapper.querySelector('.form__group_phone'),
                btnQuestion = questionsFormWrapper.querySelector('.btn_question-step'),
                btnFinal = questionsFormWrapper.querySelector('.btn_final-step');

            if ( btnQuestion ) {
                btnQuestion.addEventListener('click', (e) => {
                    e.preventDefault();
                    inputName.classList.toggle('active');
                    inputText.classList.toggle('active');
                    inputPhone.classList.toggle('active');
                    btnQuestion.classList.toggle('active');
                    btnFinal.classList.toggle('active');
                });
            }

        }

        return true;
    }
}
