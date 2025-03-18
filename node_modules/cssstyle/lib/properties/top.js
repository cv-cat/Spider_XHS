'use strict';

var parseMeasurement = require('../parsers').parseInheritingMeasurement;

module.exports.definition = {
  set: function (v) {
    this._setProperty('top', parseMeasurement(v));
  },
  get: function () {
    return this.getPropertyValue('top');
  },
  enumerable: true,
  configurable: true,
};
