import Base from 'js_core/base-controller-js';

export default class Footer extends Base {

    /**
     * Инициализация
     *
     * @returns {boolean}
     * @private
     */
    _init() {

        this.target = document.querySelector('[data-dropdown="footer-dropdown"]');
        this.content = document.querySelector('[data-dropdown="footer-dropdown-content"]');

        return !! this.target;
    }

    /**
     * Бинд событий
     *
     * @returns {boolean}
     * @private
     */
    _bind() {

        this.target.addEventListener('click', (e) => {
            this.isActive();
        });

        return true;
    }

    isActive() {

        let dropdown = this.target;
        let content = this.content;

        if (this.content) {
            if (dropdown.classList.contains('active') && content.classList.contains('active')) {
                dropdown.classList.remove('active');
                content.classList.remove('active');
            } else {
                dropdown.classList.add('active');
                content.classList.add('active');
            }
        }
    }
}
