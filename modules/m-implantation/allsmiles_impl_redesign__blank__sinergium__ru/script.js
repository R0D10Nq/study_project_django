import Base from 'js_core/base-controller';
import Swiper from 'swiper';
import {Navigation, Pagination} from 'swiper/modules';

export default class ImplantationSlider extends Base {

    /**
     * Инициализация
     *
     * @returns {boolean}
     * @private
     */
    _init() {
        this.implantationSlider = document.querySelector('[data-js-slider="implantation"]');

        return !! this.implantationSlider;
    }

    /**
     * Бинд событий
     *
     * @returns {boolean}
     * @private
     */
    _bind() {

        ['load', 'resize', 'orientationchange'].forEach((event) => {
            window.addEventListener(event, (e) => {

                let implantationSlider = new Swiper(this.implantationSlider, {
                    modules: [Navigation, Pagination],
                    slidesPerView: 'auto',
                    autoHeight: true,
                    spaceBetween: 13,
                    loop: true,
                    navigation: {
                        nextEl: ".implantation__button-next",
                        prevEl: ".implantation__button-prev",
                    },
                    breakpoints: {
                        1320: {
                            slidesPerView: 'auto',
                        },
                    },
                });
            })
        })


        return true;
    }
}
