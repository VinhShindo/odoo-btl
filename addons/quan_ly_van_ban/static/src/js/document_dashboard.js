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
            this.$('#approval_rate').text((data.approval_rate || 0).toFixed(1) + '%');
            this.$('#ai_docs').text(data.ai_docs || 0);
            
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
            
            this.charts.typeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        data: Object.values(data),
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
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
                        backgroundColor: '#f5576c'
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
        },
        
        _renderInOutChart: function(incoming, outgoing) {
            var ctx = document.getElementById('chart_incoming_outgoing');
            if (!ctx) return;
            if (this.charts.inOutChart) this.charts.inOutChart.destroy();
            
            this.charts.inOutChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Văn bản Đến', 'Văn bản Đi'],
                    datasets: [{ data: [incoming, outgoing], backgroundColor: ['#4BC0C0', '#FF9F40'] }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
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
                        backgroundColor: ['#667eea', '#e0e0e0']
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
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
                                <div style="font-size: 12px; color: #999; margin-top: 4px;">${doc.created}</div>
                            </div>
                            <span class="recent-item-status">${doc.status}</span>
                        </div>
                    `;
                }).join(''));
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