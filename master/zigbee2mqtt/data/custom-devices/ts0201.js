const fz = require('zigbee-herdsman-converters/converters/fromZigbee');
const tz = require('zigbee-herdsman-converters/converters/toZigbee');
const exposes = require('zigbee-herdsman-converters/lib/exposes');
const e = exposes.presets;
const ea = exposes.access;

module.exports = [
    {
        fingerprint: [{modelID: 'TY0201', manufacturerName: 'by _TZ3000_bjawzodf'}],  // Adjust if needed
        model: 'TS0201',
        vendor: 'TuYa',
        description: 'Temperature and humidity sensor',
        fromZigbee: [fz.temperature, fz.humidity, fz.battery],
        toZigbee: [],
        exposes: [e.temperature(), e.humidity(), e.battery()],
    },
];