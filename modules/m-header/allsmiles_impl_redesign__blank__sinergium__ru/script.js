import Base from 'js_core/base-controller-js';

export default class Header extends Base {

    _init() {

        return true;
    }

    _bind() {

        let btnClose = document.querySelector('[data-menu-close]'),
            btnOpen = document.querySelector('[data-menu-open]'),
            content = document.querySelector('[data-menu]'),
            headerFixed = document.querySelector('[data-js="header-fixed"]'),
            header = document.querySelector('[data-js-header="header"]'),
            modal = document.querySelector('[data-menu]'),
            sticky = header.offsetTop,
            menuItem = document.querySelectorAll('[data-js="menu_item"]'),
            sections = document.querySelectorAll('[data-js-scroll-target]');

        this.toggleContent(btnClose, content);
        this.toggleContent(btnOpen, content);

        menuItem.forEach(item => {

            item.addEventListener('click', (e) => {
                for ( let el of menuItem ) {
                    el.classList.remove('active');
                }

                item.classList.add('active');
            })
        })

        document.addEventListener('click', (e) => {

            if (e.target != modal && e.target != btnOpen) {
                modal.classList.add('hide');
                document.body.classList.remove('overlay');
            }
        });

        document.addEventListener('scroll', () => {

            sections.forEach(function(section, index) {
                let rect = section.getBoundingClientRect();

                if (rect.top > 0 && rect.bottom <= window.innerHeight) {

                    menuItem.forEach(item => {
                        let s = section.getAttribute('data-js-scroll-target'),
                            m = item.getAttribute('data-js-scroll-to');

                        if ( s === m ) {
                            item.classList.add('active');
                        } else {
                            item.classList.remove('active');
                        }
                    })
                }
            });

            if (window.innerWidth <= 767) {

                if (window.scrollY > sticky) {
                    header.classList.add('fixed');
                    headerFixed.classList.remove('sticky');
                } else {
                    header.classList.remove('fixed');
                }

            } else {

                if (window.scrollY > sticky) {
                    headerFixed.classList.add('sticky');
                } else {
                    headerFixed.classList.remove('sticky');
                }

            }

        });

        return true;
    }

    toggleContent(btn, content) {
        btn.addEventListener('click', () => {

            if (content.className.includes('hide')) {
                content.classList.remove('hide');
                document.body.classList.add('overlay');
            } else {
                content.classList.add('hide');
                document.body.classList.remove('overlay');
            }

        })
    }
}
