odoo.define('quan_ly_van_ban.document_dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    
    var DocumentDashboard = AbstractAction.extend({
        template: 'quan_ly_van_ban.document_dashboard_template',
        
        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.charts = {};
        },
        
        start: function() {
            this._loadChartsLibrary();
            return this._super.apply(this, arguments);
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
                    .done(function() { self._loadDashboardData(); });
            } else {
                this._loadDashboardData();
            }
        },
        
        _loadDashboardData: function() {
            var self = this;
            this._rpc({
                route: '/dashboard/document/data',
                params: {}
            }).then(function(result) {
                if (result.status === 'success') {
                    self._renderDashboard(result.data);
                }
            }).catch(function(error) {
                console.error('Error:', error);
            });
        },
        
        _renderDashboard: function(data) {
            this.$('#total_documents').text(data.total_docs || 0);
            this.$('#approved_docs').text(data.approved_docs || 0);
            this.$('#pending_docs').text(data.pending_docs || 0);
            this.$('#draft_docs').text(data.draft_docs || 0);
            this.$('#archived_docs').text(data.archived_docs || 0);
            this.$('#ocr_completed').text(data.ocr_completed || 0);
            this.$('#ocr_pending').text(data.ocr_pending || 0);
            this.$('#incoming_docs').text(data.incoming || 0);
            this.$('#outgoing_docs').text(data.outgoing || 0);
            
            if (typeof Chart !== 'undefined') {
                this._renderTypeChart(data.doc_by_type || {});
                this._renderStatusChart(data.doc_status || {});
                this._renderInOutChart(data.incoming || 0, data.outgoing || 0);
                this._renderAIChart(data.ai_docs || 0, data.total_docs || 0);
            }
            
            this._renderApprovalGauge(data.approval_rate || 0, data.approved_docs || 0, data.total_docs || 0);
            this._renderRecentDocuments(data.recent_docs || []);
        },
        
        _renderTypeChart: function(data) {
            var ctx = document.getElementById('chart_doc_by_type');
            if (!ctx) return;
            if (this.charts.typeChart) this.charts.typeChart.destroy();

            var labels = Object.keys(data);
            var values = Object.values(data);
            if (!labels.length) {
                labels = ['Không có dữ liệu'];
                values = [1];
            }
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);

            this.charts.typeChart = new Chart(ctx, {
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
        
        _renderStatusChart: function(data) {
            var ctx = document.getElementById('chart_doc_status');
            if (!ctx) return;
            if (this.charts.statusChart) this.charts.statusChart.destroy();

            this.charts.statusChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        label: 'Số văn bản',
                        data: Object.values(data),
                        backgroundColor: '#fb7185',
                        borderRadius: 8,
                        borderSkipped: false,
                        barPercentage: 0.7,
                        categoryPercentage: 0.75
                    }]
                },
                options: this._getBarChartOptions()
            });
        },
        
        _renderInOutChart: function(incoming, outgoing) {
            var ctx = document.getElementById('chart_incoming_outgoing');
            if (!ctx) return;
            if (this.charts.inOutChart) this.charts.inOutChart.destroy();

            var values = [incoming, outgoing];
            var total = values.reduce(function(sum, val) { return sum + val; }, 0);

            this.charts.inOutChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Văn bản Đến', 'Văn bản Đi'],
                    datasets: [{
                        data: values,
                        backgroundColor: ['#4BC0C0', '#f97316'],
                        borderWidth: 0,
                        borderRadius: 8,
                        hoverOffset: 14
                    }]
                },
                plugins: [this._getCenterTextPlugin(total, 'Tổng')],
                options: this._getDonutChartOptions()
            });
        },
        
        _renderAIChart: function(aiDocs, totalDocs) {
            var ctx = document.getElementById('chart_ai_summary');
            if (!ctx) return;
            if (this.charts.aiChart) this.charts.aiChart.destroy();

            this.charts.aiChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Có OCR', 'Chưa OCR'],
                    datasets: [{
                        label: 'Số văn bản',
                        data: [aiDocs, totalDocs - aiDocs],
                        backgroundColor: ['#60a5fa', 'rgba(255,255,255,0.18)'],
                        borderRadius: 8,
                        borderSkipped: false,
                        barPercentage: 0.7,
                        categoryPercentage: 0.75
                    }]
                },
                options: this._getBarChartOptions()
            });
        },
        
        _renderApprovalGauge: function(rate, approved, total) {
            var container = this.$('#gauge_approval');
            if (!container.length) return;
            
            container.html(`
                <div style="text-align: center;">
                    <div style="font-size: 48px; font-weight: bold; color: #f5576c;">
                        ${rate.toFixed(1)}%
                    </div>
                    <div style="color: #666; margin-top: 10px;">
                        ${approved} / ${total} văn bản được phê duyệt
                    </div>
                    <div style="margin-top: 20px; height: 8px; background: #e0e0e0; border-radius: 4px;">
                        <div style="height: 100%; width: ${rate}%; background: linear-gradient(90deg, #f093fb, #f5576c);"></div>
                    </div>
                </div>
            `);
        },
        
        _renderRecentDocuments: function(docs) {
            var container = this.$('#recent_documents');
            if (!container.length) return;
            
            if (docs.length > 0) {
                container.html(docs.map(function(doc) {
                    return `
                        <div class="recent-item">
                            <div>
                                <div class="recent-item-name">${_.escape(doc.name)}</div>
                                <div class="recent-item-meta">
                                    <span>${_.escape(doc.doc_type)}</span>
                                    <span>&middot;</span>
                                    <span>${_.escape(doc.responsible)}</span>
                                </div>
                                <div class="recent-item-date">${doc.created}</div>
                            </div>
                            <span class="recent-item-status">${doc.status}</span>
                        </div>
                    `;
                }).join(''));
            } else {
                container.html('<div class="loading-spinner"><i class="fa fa-folder-open"></i><div>Không có văn bản gần đây.</div></div>');
            }
        },
        
        destroy: function() {
            Object.values(this.charts).forEach(function(chart) {
                if (chart && chart.destroy) chart.destroy();
            });
            this._super.apply(this, arguments);
        }
    });
    
    core.action_registry.add('document_dashboard_action', DocumentDashboard);
    
    return DocumentDashboard;
});