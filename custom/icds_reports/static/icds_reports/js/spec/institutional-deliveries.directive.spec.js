/* global module, inject, chai */
"use strict";

var pageData = hqImport('hqwebapp/js/initial_page_data');


describe('Institutional Deliveries Directive', function () {

    var $scope, $httpBackend, $location, controller;

    pageData.registerUrl('icds-ng-template', 'template');
    pageData.registerUrl('institutional_deliveries', 'institutional_deliveries');
    pageData.registerUrl('icds_locations', 'icds_locations');

    beforeEach(module('icdsApp', function ($provide) {
        $provide.constant("userLocationId", null);
    }));

    beforeEach(inject(function ($rootScope, $compile, _$httpBackend_, _$location_) {
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $location = _$location_;

        $httpBackend.expectGET('template').respond(200, '<div></div>');
        $httpBackend.expectGET('institutional_deliveries').respond(200, {
            report_data: ['report_test_data'],
        });
        var element = window.angular.element("<institutional_deliveries data='test'></institutional_deliveries>");
        var compiled = $compile(element)($scope);

        $httpBackend.flush();
        $scope.$digest();
        controller = compiled.controller('institutionalDeliveries');
        controller.step = 'map';
    }));

    it('tests instantiate the controller properly', function () {
        chai.expect(controller).not.to.be.a('undefined');
    });

    it('tests initial state', function () {
        assert.equal(controller.mode, 'map');
        assert.equal(controller.steps['map'].label, 'Map View: National');
        assert.deepEqual(controller.filtersData, {});
    });

    it('tests supervisor location', function () {
        controller.filtersData.location_id = 'test-id';

        $httpBackend.expectGET('icds_locations?location_id=test-id').respond(200, {location_type: 'supervisor'});
        $httpBackend.expectGET('institutional_deliveries?location_id=test-id').respond(200, {
            report_data: ['report_test_data'],
        });
        controller.init();
        $httpBackend.flush();
        assert.equal(controller.mode, 'sector');
        assert.equal(controller.steps['map'].label, 'Sector View');
        assert.deepEqual(controller.data.mapData, ['report_test_data']);
    });

    it('tests non supervisor location', function () {
        controller.filtersData.location_id = 'test-id';

        $httpBackend.expectGET('icds_locations?location_id=test-id').respond(200, {location_type: 'non supervisor'});
        $httpBackend.expectGET('institutional_deliveries?location_id=test-id').respond(200, {
            report_data: ['report_test_data'],
        });
        controller.init();
        $httpBackend.flush();
        assert.equal(controller.mode, 'map');
        assert.equal(controller.steps['map'].label, 'Map View: Non supervisor');
        assert.deepEqual(controller.data.mapData, ['report_test_data']);
    });

    it('tests template popup', function () {
        var result = controller.templatePopup({properties: {name: 'test'}}, {all: 10, children: 5});
        assert.equal(result, '<div class="hoverinfo" style="max-width: 200px !important;">' +
            '<p>test</p>'
            + '<div>Total number of pregnant women who delivered in the last month: <strong>10</strong></div>'
            + '<div>Total number of pregnant women who delivered in a public/private medical facilitiy in the last month: <strong>5</strong></div>'
            + '<div>% pregnant women who delivered in a public or private medical facility in the last month: <strong>50.00%</strong></div>');
    });

    it('tests location change', function () {
        controller.init();
        controller.selectedLocations.push(
            {name: 'name1', location_id: 'test_id1'},
            {name: 'name2', location_id: 'test_id2'},
            {name: 'name3', location_id: 'test_id3'},
            {name: 'name4', location_id: 'test_id4'},
            {name: 'name5', location_id: 'test_id5'},
            {name: 'name6', location_id: 'test_id6'}
        );
        $httpBackend.expectGET('institutional_deliveries').respond(200, {
            report_data: ['report_test_data'],
        });
        $scope.$digest();
        $httpBackend.flush();
        assert.equal($location.search().location_id, 'test_id4');
        assert.equal($location.search().selectedLocationLevel, 3);
        assert.equal($location.search().location_name, 'name4');
    });

    it('tests moveToLocation national', function () {
        controller.moveToLocation('national', -1);

        var searchData = $location.search();

        assert.equal(searchData.location_id, '');
        assert.equal(searchData.selectedLocationLevel, -1);
        assert.equal(searchData.location_name, '');
    });

    it('tests moveToLocation not national', function () {
        controller.moveToLocation({location_id: 'test-id', name: 'name'}, 3);

        var searchData = $location.search();

        assert.equal(searchData.location_id, 'test-id');
        assert.equal(searchData.selectedLocationLevel, 3);
        assert.equal(searchData.location_name, 'name');
    });

    it('tests show all locations', function () {
        controller.all_locations.push(
            {name: 'name1', location_id: 'test_id1'}
        );
        var locations = controller.showAllLocations();
        assert.equal(locations, true);
    });

    it('tests not show all locations', function () {
        controller.all_locations.push(
            {name: 'name1', location_id: 'test_id1'},
            {name: 'name2', location_id: 'test_id2'},
            {name: 'name3', location_id: 'test_id3'},
            {name: 'name4', location_id: 'test_id4'},
            {name: 'name5', location_id: 'test_id5'},
            {name: 'name6', location_id: 'test_id6'},
            {name: 'name7', location_id: 'test_id7'},
            {name: 'name8', location_id: 'test_id8'},
            {name: 'name9', location_id: 'test_id9'},
            {name: 'name10', location_id: 'test_id10'}
        );
        var locations = controller.showAllLocations();
        assert.equal(locations, false);
    });

    it('tests chart options', function () {
        var chart = controller.chartOptions.chart;
        var caption = controller.chartOptions.caption;
        assert.notEqual(chart, null);
        assert.notEqual(caption, null);
        assert.equal(controller.chartOptions.chart.type, 'lineChart');
        assert.deepEqual(controller.chartOptions.chart.margin, {
            top: 20,
            right: 60,
            bottom: 60,
            left: 80,
        });
        assert.equal(controller.chartOptions.chart.clipVoronoi, false);
        assert.equal(controller.chartOptions.chart.tooltips, true);
        assert.equal(controller.chartOptions.chart.xAxis.axisLabel, '');
        assert.equal(controller.chartOptions.chart.xAxis.showMaxMin, true);
        assert.equal(controller.chartOptions.chart.xAxis.axisLabelDistance, -100);
        assert.equal(controller.chartOptions.chart.yAxis.axisLabel, '');
        assert.equal(controller.chartOptions.chart.yAxis.axisLabelDistance, 20);
        assert.equal(controller.chartOptions.caption.enable, true);
        assert.deepEqual(controller.chartOptions.caption.css, {
            'text-align': 'center',
            'margin': '0 auto',
            'width': '900px',
        });
        assert.equal(controller.chartOptions.caption.html,
            '<i class="fa fa-info-circle"></i> ' +
            'Percentage of pregnant women who delivered in a public or private medical facility in the last month. \n' +
            '\n' +
            'Delivery in medical instituitions is associated with a decrease in maternal mortality rate'
        );
    });

    it('tests chart tooltip content', function () {
        var data = {in_month: 5, y: 0.72, all: 10};
        var month = {value: "Jul 2017", series: []};

        var expected = '<p><strong>Jul 2017</strong></p><br/>'
            + '<p>Total number of pregnant women who delivered in the last month: <strong>10</strong></p>'
            + '<p>Total number of pregnant women who delivered in a public/private medical facilitiy in the last month: <strong>5</strong></p>'
            + '<p>% pregnant women who delivered in a public or private medical facility in the last month: <strong>72.00%</strong></p>';

        var result = controller.tooltipContent(month.value, data);
        assert.equal(expected, result);
    });

    it('tests disable locations for user', function () {
        controller.userLocationId = 'test_id4';
        controller.location = {name: 'name4', location_id: 'test_id4'};
        controller.selectedLocations.push(
            {name: 'name1', location_id: 'test_id1'},
            {name: 'name2', location_id: 'test_id2'},
            {name: 'name3', location_id: 'test_id3'},
            {name: 'name4', location_id: 'test_id4'},
            {name: 'name5', location_id: 'test_id5'},
            {name: 'name6', location_id: 'test_id6'}
        );
        var index = controller.getDisableIndex();
        assert.equal(index, 3);
    });
});
