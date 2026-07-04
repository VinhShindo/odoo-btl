odoo.define('nhan_su.nhan_su_dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    
    var NhanSuDashboard = AbstractAction.extend({
        template: 'nhan_su.hr_dashboard_template',
        
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

        _getTooltipConfig: function() {
            return {
                backgroundColor: '#ffffff',
                titleColor: '#0f172a',
                bodyColor: '#334155',
                borderColor: '#e2e8f0',
                borderWidth: 1,
                padding: 10,
                cornerRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            };
        },

        _getBarChartOptions: function() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { tooltip: this._getTooltipConfig(), legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#e2e8f0' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b', maxRotation: 30, minRotation: 0 } }
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
                        align: 'center',
                        maxWidth: 280,   // ⭐ QUAN TRỌNG: Giới hạn chiều rộng tối đa của Legend để chia cột đẹp hơn
                        labels: { 
                            color: '#64748b', 
                            usePointStyle: true, 
                            pointStyle: 'circle', 
                            padding: 12,      // Khoảng cách giữa các dòng
                            font: { size: 11 } // Giảm nhẹ font chữ để dễ xếp hàng
                        }
                    }
                },
                animation: { duration: 600, easing: 'easeOutQuart' },
                resizeDelay: 0 
            };
        },

        _getCenterTextPlugin: function(value, label) {
            return {
                id: 'centerText_' + Math.random().toString(36).substr(2, 6),
                afterDraw: function(chart) {
                    var ctx = chart.ctx, width = chart.width, height = chart.height;
                    ctx.save();
                    ctx.font = '700 20px Inter, ui-sans-serif';
                    ctx.fillStyle = '#0f172a';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, width / 2, height / 2 - 28);
                    ctx.font = '400 12px Inter, ui-sans-serif';
                    ctx.fillStyle = '#64748b';
                    ctx.fillText(label || 'Tổng', width / 2, height / 2 - 8);
                    ctx.restore();
                }
            };
        },

        _loadChartsLibrary: function() {
            var self = this;
            if (typeof Chart === 'undefined') {
                $.getScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js')
                    .done(function() { self._loadDashboardData(); });
            } else {
                this._loadDashboardData();
            }
        },
        
        _loadDashboardData: function() {
            var self = this;
            this._rpc({ route: '/dashboard/nhan_su/data', params: {} })
            .then(function(result) {
                if (result.status === 'success') self._renderDashboard(result.data);
            }).catch(console.error);
        },
        
        _renderDashboard: function(data) {
            this.$('#total_employees').text(data.total_employees || 0);
            this.$('#avg_age').text((data.avg_age || 0).toFixed(1) + ' tuổi');
            this.$('#total_certs').text(data.total_certifications || 0);
            var totalProjects = 0;
            if (data.project_dist) totalProjects = Object.values(data.project_dist).reduce((a, b) => a + b, 0);
            this.$('#total_projects').text(totalProjects);
            
            if (typeof Chart !== 'undefined') {
                this._renderDepartmentChart(data.emp_by_dept || {});
                this._renderPositionChart(data.emp_by_pos || {});
                this._renderCertificationChart(data.cert_dist || {});
                this._renderProjectChart(data.project_dist || {});
            }
            this._renderAgeGauge(data.avg_age || 0);
            this._renderRecentEmployees(data.recent_employees || []);
        },
        
        _renderDepartmentChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_dept');
            if (!ctx) return;
            if (this.charts.deptChart) this.charts.deptChart.destroy();
            var labels = Object.keys(data), values = Object.values(data);
            if (!labels.length) { labels = ['Không có dữ liệu']; values = [1]; }
            var total = values.reduce((a,b) => a+b, 0);
            this.charts.deptChart = new Chart(ctx, {
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
        
        _renderPositionChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_pos');
            if (!ctx) return;
            if (this.charts.posChart) this.charts.posChart.destroy();
            var labels = Object.keys(data).map(function(label) {
                if (label.includes('Quản lý Dự án')) return 'Quản lý Dự án';
                if (label.includes('Kỹ sư Giải pháp IoT')) return 'Kỹ sư IoT';
                if (label.includes('Chuyên viên Vận hành')) return 'Ch.viên Vận hành';
                if (label.includes('Chuyên viên QA')) return 'Ch.viên QA';
                if (label.includes('Kỹ sư Hệ thống IoT')) return 'Kỹ sư Hệ thống';
                if (label.includes('Chuyên viên Kinh doanh')) return 'Ch.viên K. doanh';
                return label.length > 20 ? label.substring(0, 18) + '...' : label;
            });
            var values = Object.values(data);
            if (!labels.length) { labels = ['Không có dữ liệu']; values = [0]; }
            this.charts.posChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{ label: 'Số nhân viên', data: values, backgroundColor: '#3b82f6', borderRadius: 6 }]
                },
                options: this._getBarChartOptions()
            });
        },
        
        _renderCertificationChart: function(data) {
            var ctx = document.getElementById('chart_certs');
            if (!ctx) return;
            if (this.charts.certChart) this.charts.certChart.destroy();
            var labels = Object.keys(data), values = Object.values(data);
            if (!labels.length) { labels = ['Không có dữ liệu']; values = [1]; }
            var total = values.reduce((a,b) => a+b, 0);
            this.charts.certChart = new Chart(ctx, {
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
        
        _renderProjectChart: function(data) {
            var ctx = document.getElementById('chart_projects');
            if (!ctx) return;
            if (this.charts.projectChart) this.charts.projectChart.destroy();
            var labels = Object.keys(data), values = Object.values(data);
            if (labels.length > 0) {
                this.charts.projectChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels.slice(0, 15),
                        datasets: [{
                            label: 'Số gán dự án',
                            data: values.slice(0, 15),
                            backgroundColor: '#14b8a6',
                            borderRadius: 6
                        }]
                    },
                    options: Object.assign({}, this._getBarChartOptions(), { 
                        indexAxis: 'y',
                        scales: {
                            y: { ticks: { font: { size: 10 } } }
                        }
                    })
                });
            }
        },
        
        _renderAgeGauge: function(age) {
            var container = this.$('#gauge_age');
            if (!container.length) return;
            var percentage = Math.min((age / 65) * 100, 100);
            container.html(`
                <div style="text-align: center; width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                    <div style="font-size: 40px; font-weight: 700; color: #0f172a;">${age.toFixed(1)}</div>
                    <div style="color: #64748b; margin-top: 4px; font-size: 14px;">tuổi trung bình</div>
                    <div style="margin-top: 20px; height: 6px; width: 80%; background: #e2e8f0; border-radius: 10px; overflow: hidden;">
                        <div style="height: 100%; width: ${percentage}%; background: linear-gradient(90deg, #3b82f6, #14b8a6);"></div>
                    </div>
                </div>
            `);
        },
        
        _renderRecentEmployees: function(employees) {
            var container = this.$('#recent_employees');
            if (!container.length) return;
            if (employees && employees.length > 0) {
                var self = this;
                var html = employees.map(function(emp) {
                    return `<div class="recent-item"><div class="recent-item-name">${self.escapeHtml(emp.name)}</div><div class="recent-item-details">${self.escapeHtml(emp.position)} · ${self.escapeHtml(emp.department)}</div></div>`;
                }).join('');
                container.html(html);
            } else {
                container.html('<div style="text-align: center; padding: 20px; color: #94a3b8;">Không có dữ liệu</div>');
            }
        },
        destroy: function() {
            Object.values(this.charts).forEach(function(c) { if (c && c.destroy) c.destroy(); });
            this._super.apply(this, arguments);
        }
    });
    
    core.action_registry.add('nhan_su_dashboard_action', NhanSuDashboard);
    return NhanSuDashboard;
});