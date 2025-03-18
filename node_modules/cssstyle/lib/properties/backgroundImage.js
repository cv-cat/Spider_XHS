'use strict';

var parsers = require('../parsers');

var parse = function parse(v) {
  var parsed = parsers.parseImage(v);
  if (parsed !== undefined) {
    return parsed;
  }
  return undefined;
};

module.exports.isValid = function isValid(v) {
  return parse(v) !== undefined;
};

module.exports.definition = {
  set: function (v) {
    this._setProperty('background-image', parse(v));
  },
  get: function () {
    return this.getPropertyValue('background-image');
  },
  enumerable: true,
  configurable: true,
};
