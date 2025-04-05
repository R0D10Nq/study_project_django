import Base from 'js_core/base-controller-js';
import Swiper from 'swiper';
import {Navigation, Pagination} from 'swiper/modules';

export default class WorksSlider extends Base {

    /**
     * Инициализация
     *
     * @returns {boolean}
     * @private
     */
    _init() {
        this.worksSlider = document.querySelector('[data-js-slider="works"]');
        this.btnMore = document.querySelector('[data-js-more="works-slider__more"]');

        return !! this.worksSlider;
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

                if (window.innerWidth > 767) {
                    let worksSlider = new Swiper(this.worksSlider, {
                        modules: [Navigation, Pagination],
                        slidesPerView: 1,
                        loop: true,
                        pagination: {
                            el: '.works__pagination',
                            clickable: true,
                        },
                        navigation: {
                            nextEl: ".works__button-next",
                            prevEl: ".works__button-prev",
                        }
                    });
                }
            })
        })

        this.btnMore.addEventListener('click', function (){
            document.querySelectorAll('.works-slider__slide').forEach((el) => {
                el.style.display = 'block';
                this.style.display = 'none';
            });
        });


        return true;
    }
}
