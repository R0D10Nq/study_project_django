import Base from 'js_core/base-controller-js';
import Swiper from 'swiper';
import {Navigation, Pagination} from 'swiper/modules';

export default class EmployeesSlider extends Base {

    /**
     * Инициализация
     *
     * @returns {boolean}
     * @private
     */
    _init() {
        this.employeesSlider = document.querySelector('[data-js-slider="employees"]');

        return !!this.employeesSlider;
    }

    /**
     * Бинд событий
     *
     * @returns {boolean}
     * @private
     */
    _bind() {
        const employeesSlider = new Swiper(this.employeesSlider, {
            modules: [Navigation, Pagination],
            slidesPerView: 1,
            autoHeight: true,
            loop: true,
            pagination: {
                el: '.employees__pagination',
                clickable: true,
            },
            navigation: {
                nextEl: ".employees__button-next",
                prevEl: ".employees__button-prev",
            },
        });

        return true;
    }
}
