import Base    from 'js_core/base-controller';
import CoreApp from 'js_core/core-app';

window.CoreApp = new CoreApp();

import Header from "modules/m-header/allsmiles_impl_redesign__blank__sinergium__ru/script";
import EmployeesSlider from "modules/m-employees/allsmiles_impl_redesign__blank__sinergium__ru/script";
import Question from 'modules/m-questions/allsmiles_impl_redesign__blank__sinergium__ru/script';
import Accordion from 'js_core/modules/accordion';
import WorksSlider from 'modules/m-works/allsmiles_impl_redesign__blank__sinergium__ru/script';
import ImplantationSlider from 'modules/m-implantation/allsmiles_impl_redesign__blank__sinergium__ru/script';
import Footer from 'modules/m-footer/allsmiles_impl_redesign__blank__sinergium__ru/script';
import ScrollTo from 'js_core/modules/scroll-to';
import ModalQuiz from 'modules/m-quiz/allsmiles_impl_redesign__blank__sinergium__ru/script';


class App extends Base {

    /**
     * @returns {boolean}
     */
    _init() {

        
        new Header();
        new EmployeesSlider();
        new Question();
        new Accordion();
        new WorksSlider();
        new ImplantationSlider();
        new Footer();
        new ScrollTo();
        new ModalQuiz();

        return true;
    }

    _bind() {

        return true;
    }
}

window.App = new App();
