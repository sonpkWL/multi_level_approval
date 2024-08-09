

/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { device } from "web.config";


const DateRangeGM = require('multi_level_approval.report_approval');

if (!device.isMobile) {
    patch(ControlPanel.prototype, "multi_level_approval", {
        get SearchMenuCustom(){
            return { Component: DateRangeGM, key: 'daterange' }
        }
    });
}

