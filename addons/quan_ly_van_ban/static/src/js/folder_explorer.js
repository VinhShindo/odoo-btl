odoo.define('quan_ly_van_ban.folder_explorer', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var Model = require('web.Model');
    var QWeb = core.qweb;
    var _t = core._t;

    var FolderExplorer = AbstractAction.extend({
        template: 'FolderExplorer',
        events: {
            'click .oe_kanban_folder_item': '_onFolderClick',
            'click .btn-back': '_onBackClick',
            'click .btn-home': '_onHomeClick',
            'click .btn-create-folder': '_onCreateFolder',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.model = action.params.model;
            this.currentFolderId = false;
            this.breadcrumb = [];
        },

        willStart: function () {
            return this._loadFolders();
        },

        start: function () {
            this._super.apply(this, arguments);
            this._renderBreadcrumb();
            return this._loadFolders();
        },

        _loadFolders: function () {
            var self = this;
            var FolderModel = new Model('van_ban.folder');
            
            var domain = this.currentFolderId ? [['parent_id', '=', this.currentFolderId]] : [['parent_id', '=', false]];
            
            return FolderModel.query(['id', 'name', 'complete_name', 'document_count', 'child_ids'])
                .filter(domain)
                .all()
                .then(function (folders) {
                    self.folders = folders;
                    self._renderFolders();
                    
                    // Load documents in current folder
                    return self._loadDocuments();
                });
        },
        
        _loadDocuments: function () {
            var self = this;
            var DocumentModel = new Model('van_ban.document');
            
            var domain = this.currentFolderId ? [['folder_id', '=', this.currentFolderId]] : [['folder_id', '=', false]];
            
            return DocumentModel.query(['id', 'name', 'code', 'doc_type', 'date', 'status', 'file_type', 'file'])
                .filter(domain)
                .all()
                .then(function (documents) {
                    self.documents = documents;
                    self._renderDocuments();
                });
        },
        
        _renderFolders: function () {
            if (!this.folders || this.folders.length === 0) {
                this.$('.o_folders_container').html('<div class="alert alert-info">Không có thư mục con</div>');
                return;
            }
            
            var self = this;
            var html = '<div class="row">';
            _.each(this.folders, function (folder) {
                html += QWeb.render('FolderItem', {folder: folder});
            });
            html += '</div>';
            this.$('.o_folders_container').html(html);
        },
        
        _renderDocuments: function () {
            if (!this.documents || this.documents.length === 0) {
                this.$('.o_documents_container').html('<div class="alert alert-info">Không có văn bản trong thư mục này</div>');
                return;
            }
            
            var self = this;
            var html = '<div class="row">';
            _.each(this.documents, function (doc) {
                html += QWeb.render('DocumentItem', {doc: doc});
            });
            html += '</div>';
            this.$('.o_documents_container').html(html);
        },
        
        _renderBreadcrumb: function () {
            var self = this;
            var FolderModel = new Model('van_ban.folder');
            
            if (!this.currentFolderId) {
                this.$('.o_breadcrumb').html('<li class="active">Thư mục gốc</li>');
                return;
            }
            
            // Load breadcrumb path
            FolderModel.call('search_read', [[['id', '=', this.currentFolderId]]], ['name', 'parent_id'])
                .then(function (result) {
                    var path = [];
                    var current = result[0];
                    path.unshift({id: current.id, name: current.name});
                    
                    function loadParent(parentId) {
                        if (parentId) {
                            FolderModel.call('search_read', [[['id', '=', parentId]]], ['name', 'parent_id'])
                                .then(function (parent) {
                                    if (parent.length > 0) {
                                        path.unshift({id: parent[0].id, name: parent[0].name});
                                        loadParent(parent[0].parent_id[0]);
                                    } else {
                                        self.breadcrumb = path;
                                        var html = '<li><a href="#" class="btn-home">Thư mục gốc</a></li>';
                                        _.each(self.breadcrumb, function (item, index) {
                                            if (index === self.breadcrumb.length - 1) {
                                                html += '<li class="active">' + item.name + '</li>';
                                            } else {
                                                html += '<li><a href="#" data-folder-id="' + item.id + '">' + item.name + '</a></li>';
                                            }
                                        });
                                        self.$('.o_breadcrumb').html(html);
                                        self.$('.o_breadcrumb a').on('click', function (e) {
                                            e.preventDefault();
                                            var folderId = $(this).data('folder-id');
                                            if (folderId) {
                                                self.currentFolderId = folderId;
                                                self._loadFolders();
                                                self._renderBreadcrumb();
                                            } else {
                                                self.currentFolderId = false;
                                                self._loadFolders();
                                                self._renderBreadcrumb();
                                            }
                                        });
                                    }
                                });
                        } else {
                            self.breadcrumb = path;
                            var html = '<li><a href="#" class="btn-home">Thư mục gốc</a></li>';
                            _.each(self.breadcrumb, function (item, index) {
                                if (index === self.breadcrumb.length - 1) {
                                    html += '<li class="active">' + item.name + '</li>';
                                } else {
                                    html += '<li><a href="#" data-folder-id="' + item.id + '">' + item.name + '</a></li>';
                                }
                            });
                            self.$('.o_breadcrumb').html(html);
                            self.$('.o_breadcrumb a').on('click', function (e) {
                                e.preventDefault();
                                var folderId = $(this).data('folder-id');
                                if (folderId) {
                                    self.currentFolderId = folderId;
                                    self._loadFolders();
                                    self._renderBreadcrumb();
                                } else {
                                    self.currentFolderId = false;
                                    self._loadFolders();
                                    self._renderBreadcrumb();
                                }
                            });
                        }
                    }
                    
                    if (current.parent_id && current.parent_id.length > 0) {
                        loadParent(current.parent_id[0]);
                    } else {
                        self.breadcrumb = path;
                        var html = '<li><a href="#" class="btn-home">Thư mục gốc</a></li>';
                        _.each(self.breadcrumb, function (item, index) {
                            if (index === self.breadcrumb.length - 1) {
                                html += '<li class="active">' + item.name + '</li>';
                            } else {
                                html += '<li><a href="#" data-folder-id="' + item.id + '">' + item.name + '</a></li>';
                            }
                        });
                        self.$('.o_breadcrumb').html(html);
                        self.$('.o_breadcrumb a').on('click', function (e) {
                            e.preventDefault();
                            var folderId = $(this).data('folder-id');
                            if (folderId) {
                                self.currentFolderId = folderId;
                                self._loadFolders();
                                self._renderBreadcrumb();
                            } else {
                                self.currentFolderId = false;
                                self._loadFolders();
                                self._renderBreadcrumb();
                            }
                        });
                    }
                });
        },
        
        _onFolderClick: function (e) {
            var $target = $(e.currentTarget);
            var folderId = $target.data('folder-id');
            if (folderId) {
                this.currentFolderId = folderId;
                this._loadFolders();
                this._renderBreadcrumb();
            }
        },
        
        _onBackClick: function (e) {
            e.preventDefault();
            if (this.breadcrumb.length > 0) {
                var parentId = this.breadcrumb[this.breadcrumb.length - 2];
                if (parentId) {
                    this.currentFolderId = parentId.id;
                } else {
                    this.currentFolderId = false;
                }
                this._loadFolders();
                this._renderBreadcrumb();
            }
        },
        
        _onHomeClick: function (e) {
            e.preventDefault();
            this.currentFolderId = false;
            this._loadFolders();
            this._renderBreadcrumb();
        },
        
        _onCreateFolder: function (e) {
            e.preventDefault();
            var self = this;
            
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Tạo thư mục mới',
                res_model: 'van_ban.folder',
                view_mode: 'form',
                target: 'new',
                context: {
                    default_parent_id: this.currentFolderId || false
                }
            }).then(function () {
                self._loadFolders();
            });
        }
    });
    
    core.action_registry.add('folder_explorer', FolderExplorer);
    
    return FolderExplorer;
});