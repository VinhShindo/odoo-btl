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
            var map = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
        },
        
        formatCurrency: function(value) {
            return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', minimumFractionDigits: 0 }).format(value);
        },

        _getTooltipConfig: function() {
            return {
                backgroundColor: '#ffffff',
                titleColor: '#0f172a',
                bodyColor: '#334155',
                borderColor: '#e2e8f0',
                borderWidth: 1,
                padding: 10,
                cornerRadius: 8
            };
        },

        _getAxisConfig: function() {
            return {
                grid: { color: '#e2e8f0', borderColor: '#e2e8f0', drawBorder: false },
                ticks: { color: '#64748b', padding: 10 }
            };
        },

        _getBarChartOptions: function() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { tooltip: this._getTooltipConfig(), legend: { display: false } },
                scales: { x: this._getAxisConfig(), y: Object.assign({}, this._getAxisConfig(), { beginAtZero: true }) },
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
                        labels: { color: '#64748b', usePointStyle: true, pointStyle: 'circle', padding: 14 }
                    }
                },
                animation: { duration: 600, easing: 'easeOutQuart' },
                resizeDelay: 0
            };
        },

        // ================================================
        // PHẦN QUAN TRỌNG ĐÃ SỬA: Căn chính giữa tuyệt đối
        // ================================================
        _getCenterTextPlugin: function(value, label) {
            return {
                id: 'centerText_' + Math.random().toString(36).substr(2, 6),
                afterDraw: function(chart) {
                    var ctx = chart.ctx;
                    var width = chart.width;
                    var height = chart.height;
                    
                    ctx.save();
                    // Đo chiều cao dòng chữ số to để tính toán vị trí chính xác
                    ctx.font = '700 20px Inter, ui-sans-serif, system-ui';
                    var bigTextMetrics = ctx.measureText(value);
                    var bigTextHeight = bigTextMetrics.actualBoundingBoxAscent + bigTextMetrics.actualBoundingBoxDescent;

                    // Đo chiều cao dòng chữ nhỏ
                    ctx.font = '400 12px Inter, ui-sans-serif, system-ui';
                    var smallTextMetrics = ctx.measureText(label || 'Tổng');
                    var smallTextHeight = smallTextMetrics.actualBoundingBoxAscent + smallTextMetrics.actualBoundingBoxDescent;

                    // Tính toán vị trí Y chính xác để 2 dòng nằm giữa khung
                    var totalTextHeight = bigTextHeight + smallTextHeight + 4; // Cộng thêm khoảng cách giữa 2 dòng
                    var centerY = height / 2;
                    var startY = centerY - (totalTextHeight / 2) + bigTextHeight / 2;

                    // Vẽ dòng số to
                    ctx.font = '700 20px Inter, ui-sans-serif, system-ui';
                    ctx.fillStyle = '#0f172a';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, width / 2, startY - 16);

                    // Vẽ dòng chữ nhỏ
                    ctx.font = '400 12px Inter, ui-sans-serif, system-ui';
                    ctx.fillStyle = '#64748b';
                    ctx.fillText(label || 'Tổng', width / 2, startY + bigTextHeight/2 + smallTextHeight/2 + 4 - 16);
                    
                    ctx.restore();
                }
            };
        },

        _loadChartsLibrary: function() {
            var self = this;
            if (typeof Chart === 'undefined') {
                $.getScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js')
                    .done(function() { self._loadDashboardData(); })
                    .fail(function() { console.error('Failed to load Chart.js'); self._loadDashboardData(); });
            } else {
                this._loadDashboardData();
            }
        },
        
        _loadDashboardData: function() {
            var self = this;
            this._rpc({ route: '/dashboard/crm/data', params: {} })
            .then(function(result) {
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
            if (!labels.length) { labels = ['Không có dữ liệu']; values = [1]; }
            var total = values.reduce((a,b) => a+b, 0);
            
            this.charts.customerStatusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#3b82f6', '#14b8a6', '#8b5cf6', '#f97316', '#ec4899', '#eab308'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
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
                data: { labels: labels, datasets: [{ label: 'Doanh thu (VNĐ)', data: values, backgroundColor: '#3b82f6', borderRadius: 6 }] },
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
                data: { labels: labels, datasets: [{ label: 'Số báo giá', data: values, backgroundColor: '#8b5cf6', borderRadius: 6 }] },
                options: this._getBarChartOptions()
            });
        },
        
        _renderContractStatusChart: function(data) {
            var ctx = document.getElementById('chart_contract_status');
            if (!ctx) return;
            if (this.charts.contractStatusChart) this.charts.contractStatusChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) { labels = ['Không có dữ liệu']; values = [1]; }
            var total = values.reduce((a,b) => a+b, 0);
            
            this.charts.contractStatusChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#10b981', '#f97316', '#ef4444', '#3b82f6', '#8b5cf6'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
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
                        labels: customers.map(c => c.name),
                        datasets: [{ label: 'Doanh thu (VNĐ)', data: customers.map(c => c.revenue), backgroundColor: '#14b8a6', borderRadius: 6 }]
                    },
                    options: Object.assign({}, this._getBarChartOptions(), { indexAxis: 'y' })
                });
            }
        },
        
        _renderConversionGauge: function(rate, accepted, total) {
            var container = this.$('#gauge_conversion');
            if (!container.length) return;
            
            var percentage = Math.min(rate, 100);
            container.html(`
                <div style="text-align: center; width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                    <div style="font-size: 40px; font-weight: 700; color: #0f172a;">${rate.toFixed(1)}%</div>
                    <div style="color: #64748b; margin-top: 4px; font-size: 14px;">${accepted} / ${total} báo giá chấp nhận</div>
                    <div style="margin-top: 20px; height: 6px; width: 80%; background: #e2e8f0; border-radius: 10px; overflow: hidden;">
                        <div style="height: 100%; width: ${percentage}%; background: linear-gradient(90deg, #3b82f6, #14b8a6);"></div>
                    </div>
                </div>
            `);
        },
        
        destroy: function() {
            Object.values(this.charts).forEach(function(chart) { if (chart && chart.destroy) chart.destroy(); });
            this._super.apply(this, arguments);
        }
    });
    
    core.action_registry.add('crm_dashboard_action', CrmDashboard);
    return CrmDashboard;
});