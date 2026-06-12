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
        },
        
        _renderCustomerStatusChart: function(data) {
            var ctx = document.getElementById('chart_customer_status');
            if (!ctx) return;
            if (this.charts.customerStatusChart) this.charts.customerStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            
            this.charts.customerStatusChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { position: 'bottom' } }
                }
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
                        backgroundColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
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
                        backgroundColor: '#764ba2'
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        },
        
        _renderContractStatusChart: function(data) {
            var ctx = document.getElementById('chart_contract_status');
            if (!ctx) return;
            if (this.charts.contractStatusChart) this.charts.contractStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            
            this.charts.contractStatusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#4BC0C0', '#FF9F40', '#FF6384', '#36A2EB', '#FFCE56', '#9966FF']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'bottom' } }
                }
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
                        labels: customers.map(c => c.name),
                        datasets: [{
                            label: 'Doanh thu (VNĐ)',
                            data: customers.map(c => c.revenue),
                            backgroundColor: '#667eea'
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        scales: { x: { beginAtZero: true } }
                    }
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