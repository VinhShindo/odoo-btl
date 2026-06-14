odoo.define('quan_ly_khach_hang.crm_dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    
    var CrmDashboard = AbstractAction.extend({
        template: 'quan_ly_khach_hang.crm_dashboard_template',
        
        events: {},
        
        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.charts = {};
        },
        
        start: function() {
            this._loadChartsLibrary();
            return this._super.apply(this, arguments);
        },
        
        escapeHtml: function(text) {
            if (!text) return '';
            var map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
        },
        
        formatCurrency: function(value) {
            return new Intl.NumberFormat('vi-VN', {
                style: 'currency',
                currency: 'VND',
                minimumFractionDigits: 0
            }).format(value);
        },

        _getTooltipConfig: function() {
            return {
                enabled: true,
                backgroundColor: 'rgba(15,23,42,0.95)',
                titleColor: '#f8fafc',
                bodyColor: '#e2e8f0',
                borderColor: 'rgba(148,163,184,0.16)',
                borderWidth: 1,
                padding: 12,
                displayColors: false,
                intersect: false,
                mode: 'nearest',
                position: 'nearest'
            };
        },

        _getAxisConfig: function() {
            return {
                grid: {
                    color: 'rgba(148,163,184,0.12)',
                    borderColor: 'rgba(148,163,184,0.16)',
                    drawBorder: false
                },
                ticks: {
                    color: '#cbd5e1',
                    padding: 10
                }
            };
        },

        _getBarChartOptions: function() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: this._getTooltipConfig(),
                    legend: { display: false }
                },
                scales: {
                    x: this._getAxisConfig(),
                    y: Object.assign({}, this._getAxisConfig(), { beginAtZero: true })
                },
                animation: { duration: 600, easing: 'easeOutQuart' }
            };
        },

        _getDonutChartOptions: function() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: {
                    tooltip: this._getTooltipConfig(),
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 18
                        }
                    }
                },
                hoverOffset: 12,
                animation: { duration: 600, easing: 'easeOutQuart' }
            };
        },

        _getCenterTextPlugin: function(value, label) {
            var id = 'centerText_' + Math.random().toString(36).substr(2, 6);
            return {
                id: id,
                afterDraw: function(chart) {
                    var ctx = chart.ctx;
                    var width = chart.width;
                    var height = chart.height;
                    ctx.save();
                    ctx.font = '600 20px Inter, ui-sans-serif, system-ui';
                    ctx.fillStyle = '#f8fafc';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, width / 2, height / 2 - 10);
                    ctx.font = '400 12px Inter, ui-sans-serif, system-ui';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText(label || 'Tổng', width / 2, height / 2 + 14);
                    ctx.restore();
                }
            };
        },

        _loadChartsLibrary: function() {
            var self = this;
            if (typeof Chart === 'undefined') {
                $.getScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js')
                    .done(function() {
                        self._loadDashboardData();
                    })
                    .fail(function() {
                        console.error('Failed to load Chart.js');
                        self._loadDashboardData();
                    });
            } else {
                this._loadDashboardData();
            }
        },
        
        _loadDashboardData: function() {
            var self = this;
            this._rpc({
                route: '/dashboard/crm/data',
                params: {}
            }).then(function(result) {
                if (result.status === 'success') {
                    self._renderDashboard(result.data);
                } else {
                    console.error('Error:', result.message);
                }
            }).catch(function(error) {
                console.error('Error loading dashboard data:', error);
            });
        },
        
        _ensureScrollable: function() {
            var self = this;
            setTimeout(function() {
                var container = self.$('.crm-dashboard-container');
                if (container.length) {
                    // Force hardware acceleration và đảm bảo overflow
                    container.css({
                        'overflow-y': 'auto',
                        'height': '100%',
                        'display': 'block'
                    });
                    
                    // Kiểm tra và sửa các container cha bị overflow hidden
                    var parent = container.parent();
                    var maxDepth = 10;
                    var depth = 0;
                    
                    while (parent.length && !parent.is('body') && depth < maxDepth) {
                        var overflow = parent.css('overflow');
                        var overflowY = parent.css('overflow-y');
                        
                        if (overflow === 'hidden' || overflowY === 'hidden') {
                            parent.css({
                                'overflow': 'auto',
                                'overflow-y': 'auto'
                            });
                        }
                        
                        parent = parent.parent();
                        depth++;
                    }
                    
                    console.log('CRM Scroll enabled - Container height:', container[0].scrollHeight, 'Client height:', container[0].clientHeight);
                }
            }, 100);
        },
        
        _renderDashboard: function(data) {
            this.$('#total_customers').text(data.total_customers || 0);
            this.$('#total_revenue').text(this.formatCurrency(data.total_expected_revenue || 0));
            
            var totalContracts = 0;
            if (data.contract_status) {
                totalContracts = Object.values(data.contract_status).reduce((a, b) => a + b, 0);
            }
            this.$('#total_contracts').text(totalContracts);
            this.$('#conversion_rate').text((data.conversion_rate || 0).toFixed(1) + '%');
            
            if (typeof Chart !== 'undefined') {
                this._renderCustomerStatusChart(data.customer_status || {});
                this._renderRevenueByTypeChart(data.revenue_by_type || {});
                this._renderQuotationStatusChart(data.quotation_status || {});
                this._renderContractStatusChart(data.contract_status || {});
                this._renderTopCustomersChart(data.top_customers || []);
            }
            
            this._renderConversionGauge(data.conversion_rate || 0, data.accepted_quotations || 0, data.quotation_count || 0);
            
            // Đảm bảo scroll hoạt động
            this._ensureScrollable();
        },
        
        _renderCustomerStatusChart: function(data) {
            var ctx = document.getElementById('chart_customer_status');
            if (!ctx) return;
            if (this.charts.customerStatusChart) this.charts.customerStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [1];
            }
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);
            
            this.charts.customerStatusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#60a5fa', '#38bdf8', '#22c55e', '#f97316', '#c084fc', '#facc15'],
                        borderWidth: 0,
                        borderRadius: 8,
                        hoverOffset: 14
                    }]
                },
                plugins: [this._getCenterTextPlugin(total, 'Tổng')],
                options: this._getDonutChartOptions()
            });
        },
        
        _renderRevenueByTypeChart: function(data) {
            var ctx = document.getElementById('chart_revenue_by_type');
            if (!ctx) return;
            if (this.charts.revenueByTypeChart) this.charts.revenueByTypeChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            
            this.charts.revenueByTypeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Doanh thu (VNĐ)',
                        data: values,
                        backgroundColor: '#60a5fa',
                        borderRadius: 8,
                        borderSkipped: false,
                        barPercentage: 0.7,
                        categoryPercentage: 0.75
                    }]
                },
                options: this._getBarChartOptions()
            });
        },
        
        _renderQuotationStatusChart: function(data) {
            var ctx = document.getElementById('chart_quotation_status');
            if (!ctx) return;
            if (this.charts.quotationStatusChart) this.charts.quotationStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            
            this.charts.quotationStatusChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số báo giá',
                        data: values,
                        backgroundColor: '#8b5cf6',
                        borderRadius: 8,
                        borderSkipped: false,
                        barPercentage: 0.7,
                        categoryPercentage: 0.75
                    }]
                },
                options: this._getBarChartOptions()
            });
        },
        
        _renderContractStatusChart: function(data) {
            var ctx = document.getElementById('chart_contract_status');
            if (!ctx) return;
            if (this.charts.contractStatusChart) this.charts.contractStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [1];
            }
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);
            
            this.charts.contractStatusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#4BC0C0', '#f97316', '#fb7185', '#38bdf8', '#facc15', '#a78bfa'],
                        borderWidth: 0,
                        borderRadius: 8,
                        hoverOffset: 14
                    }]
                },
                plugins: [this._getCenterTextPlugin(total, 'Tổng')],
                options: this._getDonutChartOptions()
            });
        },
        
        _renderTopCustomersChart: function(customers) {
            var ctx = document.getElementById('chart_top_customers');
            if (!ctx) return;
            if (this.charts.topCustomersChart) this.charts.topCustomersChart.destroy();
            
            if (customers && customers.length > 0) {
                this.charts.topCustomersChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: customers.map(function(c) { return c.name; }),
                        datasets: [{
                            label: 'Doanh thu (VNĐ)',
                            data: customers.map(function(c) { return c.revenue; }),
                            backgroundColor: '#38bdf8',
                            borderRadius: 8,
                            borderSkipped: false,
                            barPercentage: 0.6,
                            categoryPercentage: 0.7
                        }]
                    },
                    options: Object.assign({}, this._getBarChartOptions(), {
                        indexAxis: 'y'
                    })
                });
            }
        },
        
        _renderConversionGauge: function(rate, accepted, total) {
            var container = this.$('#gauge_conversion');
            if (!container.length) return;
            
            var percentage = Math.min(rate, 100);
            container.html(`
                <div style="text-align: center;">
                    <div style="font-size: 48px; font-weight: bold; color: #667eea;">
                        ${rate.toFixed(1)}%
                    </div>
                    <div style="color: #666; margin-top: 10px;">
                        ${accepted} / ${total} báo giá được chấp nhận
                    </div>
                    <div style="margin-top: 20px; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden;">
                        <div style="height: 100%; width: ${percentage}%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s ease;"></div>
                    </div>
                </div>
            `);
        },
        
        destroy: function() {
            Object.values(this.charts).forEach(function(chart) {
                if (chart && chart.destroy) chart.destroy();
            });
            this._super.apply(this, arguments);
        }
    });
    
    core.action_registry.add('crm_dashboard_action', CrmDashboard);
    return CrmDashboard;
});