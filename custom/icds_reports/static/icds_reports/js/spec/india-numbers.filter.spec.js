/* global module, inject, chai */
"use strict";

describe('India Number Filter', function () {

    var $filter;

    beforeEach(function () {
        module('icdsApp');

        inject(function (_$filter_) {
            $filter = _$filter_;
        });
    });

    it('tests instantiate the filter properly', function () {
        chai.expect($filter).not.to.be.a('undefined');
    });

    it('tests filter null value', function () {
        // Arrange.
        var testValue = null;

        // Act.
        var result = $filter('indiaNumbers')(testValue);

        //Expected
        var expected = '0';

        // Assert.
        assert.equal(expected, result);
    });

    it('tests filter last three values', function () {
        // Arrange.
        var testValue = 500.000;

        // Act.
        var result = $filter('indiaNumbers')(testValue);

        //Expected
        var expected = '500';

        // Assert.
        assert.equal(expected, result);
    });

    it('tests filter when number is a floating point', function () {
        // Arrange.
        var testValue = 50.88;

        // Act.
        var result = $filter('indiaNumbers')(testValue);

        //Expected
        var expected = '51';

        // Assert.
        assert.equal(expected, result);
    });

    it('tests filter one hundred thousands', function () {
        // Arrange.
        var testValue = 100000;

        // Act.
        var result = $filter('indiaNumbers')(testValue);

        //Expected
        var expected = '1,00,000';

        // Assert.
        assert.equal(expected, result);
    });

    it('tests filter one billion', function () {
        // Arrange.
        var testValue = 1000000000;

        // Act.
        var result = $filter('indiaNumbers')(testValue);

        //Expected
        var expected = '1,00,00,00,000';

        // Assert.
        assert.equal(expected, result);
    });
});
