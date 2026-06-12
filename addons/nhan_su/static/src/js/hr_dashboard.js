odoo.define('nhan_su.hr_dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    
    var HrDashboard = AbstractAction.extend({
        template: 'nhan_su.hr_dashboard_template',  // Module.template_id
        
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
        },
        
        _renderDepartmentChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_dept');
            if (!ctx) return;
            if (this.charts.deptChart) this.charts.deptChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (labels.length === 0) {
                labels.push('Không có dữ liệu');
                values.push(1);
            }
            
            this.charts.deptChart = new Chart(ctx, {
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
        
        _renderPositionChart: function(data) {
            var ctx = document.getElementById('chart_emp_by_pos');
            if (!ctx) return;
            if (this.charts.posChart) this.charts.posChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (labels.length === 0) {
                labels.push('Không có dữ liệu');
                values.push(0);
            }
            
            this.charts.posChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số nhân viên',
                        data: values,
                        backgroundColor: '#4facfe'
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        },
        
        _renderCertificationChart: function(data) {
            var ctx = document.getElementById('chart_certs');
            if (!ctx) return;
            if (this.charts.certChart) this.charts.certChart.destroy();
            
            var labels = Object.keys(data);
            var values = Object.values(data);
            if (labels.length === 0) {
                labels.push('Không có dữ liệu');
                values.push(1);
            }
            
            this.charts.certChart = new Chart(ctx, {
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
                            backgroundColor: '#00f2fe'
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
                    }
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