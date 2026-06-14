odoo.define('nhan_su.hr_dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    
    var HrDashboard = AbstractAction.extend({
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
            var map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
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
                route: '/dashboard/hr/data',
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
            this.$('#total_employees').text(data.total_employees || 0);
            this.$('#avg_age').text((data.avg_age || 0).toFixed(1) + ' tuổi');
            this.$('#total_certs').text(data.total_certifications || 0);
            
            var totalProjects = 0;
            if (data.project_dist) {
                totalProjects = Object.values(data.project_dist).reduce((a, b) => a + b, 0);
            }
            this.$('#total_projects').text(totalProjects);
            
            if (typeof Chart !== 'undefined') {
                this._renderDepartmentChart(data.emp_by_dept || {});
                this._renderPositionChart(data.emp_by_pos || {});
                this._renderCertificationChart(data.cert_dist || {});
                this._renderProjectChart(data.project_dist || {});
            }
            
            this._renderAgeGauge(data.avg_age || 0);
            this._renderRecentEmployees(data.recent_employees || []);
            
            // Đảm bảo scroll hoạt động
            this._ensureScrollable();
        },
        
        _ensureScrollable: function() {
            var self = this;
            setTimeout(function() {
                var container = self.$('.hr-dashboard-container');
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
                    
                    // Log để debug
                    console.log('Scroll enabled - Container height:', container[0].scrollHeight, 'Client height:', container[0].clientHeight);
                }
            }, 100);
        },
        
        _renderDepartmentChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_dept');
            if (!ctx) return;
            if (this.charts.deptChart) this.charts.deptChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [1];
            }
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);
            
            this.charts.deptChart = new Chart(ctx, {
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
        
        _renderPositionChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_pos');
            if (!ctx) return;
            if (this.charts.posChart) this.charts.posChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [0];
            }
            
            this.charts.posChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số nhân viên',
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
        
        _renderCertificationChart: function(data) {
            var ctx = document.getElementById('chart_certs');
            if (!ctx) return;
            if (this.charts.certChart) this.charts.certChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [1];
            }
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);
            
            this.charts.certChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#34d399', '#f97316', '#fb7185', '#38bdf8', '#facc15', '#a78bfa'],
                        borderWidth: 0,
                        borderRadius: 8,
                        hoverOffset: 14
                    }]
                },
                plugins: [this._getCenterTextPlugin(total, 'Tổng')],
                options: this._getDonutChartOptions()
            });
        },
        
        _renderAgeGauge: function(age) {
            var container = this.$('#gauge_age');
            if (!container.length) return;
            
            var percentage = Math.min((age / 65) * 100, 100);
            container.html(`
                <div style="text-align: center;">
                    <div style="font-size: 48px; font-weight: bold; color: #4facfe;">
                        ${age.toFixed(1)}
                    </div>
                    <div style="color: #666; margin-top: 10px;">tuổi trung bình</div>
                    <div style="margin-top: 20px; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden;">
                        <div style="height: 100%; width: ${percentage}%; background: linear-gradient(90deg, #4facfe, #00f2fe);"></div>
                    </div>
                </div>
            `);
        },
        
        _renderProjectChart: function(data) {
            var ctx = document.getElementById('chart_projects');
            if (!ctx) return;
            if (this.charts.projectChart) this.charts.projectChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            
            if (labels.length > 0) {
                this.charts.projectChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Số gán dự án',
                            data: values,
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
        
        _renderRecentEmployees: function(employees) {
            var container = this.$('#recent_employees');
            if (!container.length) return;
            
            if (employees && employees.length > 0) {
                var self = this;
                var html = employees.map(function(emp) {
                    return `
                        <div class="recent-item">
                            <div>
                                <div class="recent-item-name">${self.escapeHtml(emp.name)}</div>
                                <div class="recent-item-details">
                                    ${self.escapeHtml(emp.position)} - ${self.escapeHtml(emp.department)}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                container.html(html);
            } else {
                container.html('<div style="text-align: center; padding: 20px; color: #999;">Không có dữ liệu</div>');
            }
        },
        
        destroy: function() {
            Object.values(this.charts).forEach(function(chart) {
                if (chart && chart.destroy) chart.destroy();
            });
            this._super.apply(this, arguments);
        }
    });
    
    core.action_registry.add('hr_dashboard_action', HrDashboard);
    return HrDashboard;
});