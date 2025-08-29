// Copyright (c) 2025, Alphamonak Solutions

// Mobile-specific JavaScript for Quantity Survey Module
// Handles touch interactions, offline sync, mobile UX, AR/VR capabilities

melon.provide('quantity_survey.mobile');

quantity_survey.mobile = {
    init: function() {
        this.setup_touch_handlers();
        this.setup_offline_sync();
        this.setup_mobile_navigation();
        this.setup_gps_integration();
        this.setup_camera_integration();
        this.setup_ar_capabilities();
        this.setup_voice_recognition();
        this.setup_barcode_scanner();
    },

    setup_touch_handlers: function() {
        // Add touch-friendly interactions
        $(document).on('touchstart', '.grid-row', function(e) {
            $(this).addClass('touch-active');
        });

        $(document).on('touchend', '.grid-row', function(e) {
            $(this).removeClass('touch-active');
        });

        // Enhanced swipe gestures
        this.setup_swipe_gestures();
        this.setup_pinch_zoom();
    },

    setup_swipe_gestures: function() {
        let startX, startY, endX, endY, startTime;

        $(document).on('touchstart', function(e) {
            startX = e.originalEvent.changedTouches[0].screenX;
            startY = e.originalEvent.changedTouches[0].screenY;
            startTime = Date.now();
        });

        $(document).on('touchend', function(e) {
            endX = e.originalEvent.changedTouches[0].screenX;
            endY = e.originalEvent.changedTouches[0].screenY;
            const endTime = Date.now();
            
            quantity_survey.mobile.handle_swipe(startX, startY, endX, endY, endTime - startTime);
        });
    },

    setup_pinch_zoom: function() {
        // Enable pinch zoom for images and technical drawings
        $('.attachment-preview img, .drawing-viewer img').each(function() {
            $(this).wrap('<div class="pinch-zoom-container"></div>');
            
            // Add zoom controls
            $(this).parent().append(`
                <div class="zoom-controls">
                    <button class="btn btn-sm zoom-in"><i class="fa fa-plus"></i></button>
                    <button class="btn btn-sm zoom-out"><i class="fa fa-minus"></i></button>
                    <button class="btn btn-sm zoom-reset"><i class="fa fa-refresh"></i></button>
                </div>
            `);
        });
    },

    handle_swipe: function(startX, startY, endX, endY, duration) {
        const deltaX = endX - startX;
        const deltaY = endY - startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        // Minimum swipe distance and maximum duration for quick gestures
        if (distance < 50 || duration > 800) return;

        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal swipe
            if (deltaX > 0) {
                this.handle_swipe_right();
            } else {
                this.handle_swipe_left();
            }
        } else {
            // Vertical swipe
            if (deltaY < 0) {
                this.handle_swipe_up();
            } else {
                this.handle_swipe_down();
            }
        }
    },

    handle_swipe_right: function() {
        // Go back or show side menu
        if ($('.mobile-side-menu').is(':visible')) {
            this.hide_side_menu();
        } else if (cur_frm && cur_frm.doc.__unsaved) {
            melon.msgprint(__('Please save changes before navigating'));
        } else {
            window.history.back();
        }
    },

    handle_swipe_left: function() {
        // Show side menu or quick actions
        this.show_side_menu();
    },

    handle_swipe_up: function() {
        // Show details panel or minimize
        this.toggle_details_panel();
    },

    handle_swipe_down: function() {
        // Refresh or close details
        if ($('.details-panel').is(':visible')) {
            this.hide_details_panel();
        } else {
            this.refresh_current_view();
        }
    },

    show_side_menu: function() {
        const menu_html = `
            <div class="mobile-side-menu">
                <div class="menu-header">
                    <h4>${__('Quick Actions')}</h4>
                    <button class="btn btn-sm btn-close">×</button>
                </div>
                <div class="menu-content">
                    <div class="menu-section">
                        <h5>${__('Navigation')}</h5>
                        <button class="btn btn-block menu-item" data-action="dashboard">${__('Dashboard')}</button>
                        <button class="btn btn-block menu-item" data-action="boq">${__('BOQ')}</button>
                        <button class="btn btn-block menu-item" data-action="valuations">${__('Valuations')}</button>
                        <button class="btn btn-block menu-item" data-action="final-account">${__('Final Account')}</button>
                    </div>
                    <div class="menu-section">
                        <h5>${__('Tools')}</h5>
                        <button class="btn btn-block menu-item" data-action="camera">${__('Camera')}</button>
                        <button class="btn btn-block menu-item" data-action="gps">${__('GPS Location')}</button>
                        <button class="btn btn-block menu-item" data-action="voice">${__('Voice Input')}</button>
                        <button class="btn btn-block menu-item" data-action="barcode">${__('Scan Barcode')}</button>
                        <button class="btn btn-block menu-item" data-action="ar-measure">${__('AR Measure')}</button>
                    </div>
                    <div class="menu-section">
                        <h5>${__('Data')}</h5>
                        <button class="btn btn-block menu-item" data-action="sync">${__('Sync Offline')}</button>
                        <button class="btn btn-block menu-item" data-action="backup">${__('Backup Data')}</button>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(menu_html);
        $('.mobile-side-menu').addClass('show');
        
        // Handle menu actions
        $('.menu-item').on('click', (e) => {
            const action = $(e.target).data('action');
            this.handle_menu_action(action);
            this.hide_side_menu();
        });
        
        $('.btn-close').on('click', () => this.hide_side_menu());
    },

    hide_side_menu: function() {
        $('.mobile-side-menu').removeClass('show');
        setTimeout(() => $('.mobile-side-menu').remove(), 300);
    },

    handle_menu_action: function(action) {
        switch(action) {
            case 'dashboard':
                melon.set_route('/app/quantity-survey');
                break;
            case 'boq':
                melon.set_route('/app/boq');
                break;
            case 'valuations':
                melon.set_route('/app/valuation');
                break;
            case 'final-account':
                melon.set_route('/app/final-account');
                break;
            case 'camera':
                this.capture_photo();
                break;
            case 'gps':
                this.capture_location();
                break;
            case 'voice':
                this.start_voice_input();
                break;
            case 'barcode':
                this.scan_barcode();
                break;
            case 'ar-measure':
                this.start_ar_measurement();
                break;
            case 'sync':
                this.sync_offline_data();
                break;
            case 'backup':
                this.backup_offline_data();
                break;
        }
    },

    setup_offline_sync: function() {
        // Enhanced offline sync with IndexedDB
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/quantity-survey-sw.js')
                .then(registration => {
                    console.log('Service Worker registered');
                    this.service_worker = registration;
                    this.setup_background_sync();
                });
        }

        // Handle connectivity changes
        window.addEventListener('online', () => {
            this.handle_online();
        });

        window.addEventListener('offline', () => {
            this.handle_offline();
        });
        
        // Setup periodic sync
        this.setup_periodic_sync();
    },

    handle_online: function() {
        melon.show_alert({
            message: __('Connection restored. Syncing data...'),
            indicator: 'green'
        });
        
        this.sync_offline_data();
        this.update_connectivity_indicator(true);
    },

    handle_offline: function() {
        melon.show_alert({
            message: __('You are offline. Data will sync when connection is restored.'),
            indicator: 'orange'
        });
        
        this.update_connectivity_indicator(false);
        this.enable_offline_mode();
    },

    update_connectivity_indicator: function(online) {
        const indicator = $('.connectivity-indicator');
        if (indicator.length === 0) {
            $('body').append(`
                <div class="connectivity-indicator ${online ? 'online' : 'offline'}">
                    <i class="fa ${online ? 'fa-wifi' : 'fa-wifi-slash'}"></i>
                    <span>${online ? __('Online') : __('Offline')}</span>
                </div>
            `);
        } else {
            indicator
                .removeClass('online offline')
                .addClass(online ? 'online' : 'offline')
                .find('i')
                .removeClass('fa-wifi fa-wifi-slash')
                .addClass(online ? 'fa-wifi' : 'fa-wifi-slash');
            indicator.find('span').text(online ? __('Online') : __('Offline'));
        }
    },

    enable_offline_mode: function() {
        // Enable offline editing capabilities
        $('.melon-form').addClass('offline-mode');
        
        // Show offline notification
        this.show_offline_notification();
    },

    setup_mobile_navigation: function() {
        if (melon.utils.is_mobile()) {
            this.create_bottom_navigation();
            this.setup_floating_action_button();
        }
    },

    create_bottom_navigation: function() {
        const nav_items = [
            { label: __('Home'), icon: 'fa-home', route: '/app/quantity-survey' },
            { label: __('BOQ'), icon: 'fa-list-alt', route: '/app/boq' },
            { label: __('Measure'), icon: 'fa-ruler', action: 'ar-measure' },
            { label: __('Camera'), icon: 'fa-camera', action: 'camera' },
            { label: __('Menu'), icon: 'fa-bars', action: 'menu' }
        ];

        const nav_html = `
            <div class="mobile-bottom-nav">
                ${nav_items.map(item => `
                    <div class="nav-item ${item.route ? 'nav-route' : 'nav-action'}" 
                         data-route="${item.route || ''}" 
                         data-action="${item.action || ''}">
                        <i class="fa ${item.icon}"></i>
                        <span class="nav-label">${item.label}</span>
                    </div>
                `).join('')}
            </div>
        `;

        $('body').append(nav_html);

        // Handle navigation
        $('.nav-route').on('click', function() {
            const route = $(this).data('route');
            melon.set_route(route);
        });
        
        $('.nav-action').on('click', (e) => {
            const action = $(e.currentTarget).data('action');
            quantity_survey.mobile.handle_menu_action(action);
        });
    },

    setup_gps_integration: function() {
        this.gps_enabled = 'geolocation' in navigator;
        
        if (this.gps_enabled) {
            this.setup_location_tracking();
            this.setup_geofencing();
        }
    },

    setup_location_tracking: function() {
        // Auto-capture location for site visits
        $(document).on('form_refresh', (e, frm) => {
            if (['Valuation', 'Final Account'].includes(frm.doctype) && frm.is_new()) {
                this.capture_location(frm);
            }
        });
    },

    capture_location: function(frm) {
        if (!this.gps_enabled) return;

        melon.show_alert({
            message: __('Capturing location...'),
            indicator: 'blue'
        });

        navigator.geolocation.getCurrentPosition(
            position => {
                if (frm) {
                    melon.model.set_value(frm.doctype, frm.docname, {
                        'gps_latitude': position.coords.latitude,
                        'gps_longitude': position.coords.longitude,
                        'location_accuracy': position.coords.accuracy,
                        'location_timestamp': melon.datetime.now_datetime()
                    });
                }

                melon.show_alert({
                    message: __('Location captured (±{0}m)', [Math.round(position.coords.accuracy)]),
                    indicator: 'green'
                });
                
                // Get address from coordinates
                if (frm) this.reverse_geocode(position.coords.latitude, position.coords.longitude, frm);
            },
            error => {
                melon.show_alert({
                    message: __('Location capture failed: {0}', [error.message]),
                    indicator: 'red'
                });
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 300000
            }
        );
    },

    reverse_geocode: function(lat, lng, frm) {
        // Use a reverse geocoding service to get address
        fetch(`https://api.opencagedata.com/geocode/v1/json?q=${lat}+${lng}&key=YOUR_API_KEY`)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    const address = data.results[0].formatted;
                    melon.model.set_value(frm.doctype, frm.docname, 'location_address', address);
                }
            })
            .catch(error => console.warn('Reverse geocoding failed:', error));
    },

    // Camera integration for site photos
    setup_camera_integration: function() {
        $(document).on('click', '.btn-camera-capture', (e) => {
            this.capture_photo();
        });
    },

    capture_photo: function() {
        if ('mediaDevices' in navigator) {
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Use back camera
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                } 
            })
            .then(stream => {
                this.show_camera_modal(stream);
            })
            .catch(err => {
                melon.msgprint(__('Camera access denied: {0}', [err.message]));
            });
        }
    },

    show_camera_modal: function(stream) {
        const modal = new melon.ui.Dialog({
            title: __('Capture Photo'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'camera_preview',
                    options: `
                        <div class="camera-container">
                            <video id="camera-preview" autoplay playsinline></video>
                            <canvas id="photo-canvas" style="display:none;"></canvas>
                            <div class="camera-overlay">
                                <div class="camera-grid"></div>
                                <div class="camera-controls">
                                    <button class="btn btn-default btn-flash" id="toggle-flash">
                                        <i class="fa fa-flash"></i>
                                    </button>
                                    <button class="btn btn-default btn-flip" id="flip-camera">
                                        <i class="fa fa-refresh"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `
                }
            ],
            primary_action_label: __('Capture'),
            primary_action: () => {
                this.take_photo(stream);
                modal.hide();
            },
            secondary_action_label: __('Cancel'),
            secondary_action: () => {
                stream.getTracks().forEach(track => track.stop());
                modal.hide();
            }
        });

        modal.show();
        
        // Start video stream
        const video = modal.$wrapper.find('#camera-preview')[0];
        video.srcObject = stream;
        
        // Setup camera controls
        modal.$wrapper.find('#toggle-flash').on('click', () => this.toggle_flash(stream));
        modal.$wrapper.find('#flip-camera').on('click', () => this.flip_camera(modal, stream));
    },

    take_photo: function(stream) {
        const video = $('#camera-preview')[0];
        const canvas = $('#photo-canvas')[0];
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        // Stop the stream
        stream.getTracks().forEach(track => track.stop());

        // Add timestamp and location watermark
        this.add_photo_metadata(context, canvas);

        // Convert to blob and upload
        canvas.toBlob(blob => {
            this.upload_photo(blob);
        }, 'image/jpeg', 0.9);
    },

    upload_photo: function(blob) {
        const formData = new FormData();
        const filename = `site-photo-${Date.now()}.jpg`;
        formData.append('file', blob, filename);
        formData.append('is_private', 0);
        formData.append('folder', 'Home/Quantity Survey Photos');

        fetch('/api/method/upload_file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                melon.show_alert({
                    message: __('Photo uploaded successfully'),
                    indicator: 'green'
                });

                // Attach to current document if available
                if (cur_frm) {
                    cur_frm.attachments.attachment_uploaded(data.message);
                }
                
                // Store in offline database as backup
                this.store_photo_offline(data.message);
            }
        })
        .catch(error => {
            // Store offline if upload fails
            this.store_photo_offline({
                file_name: filename,
                file_data: blob,
                timestamp: Date.now()
            });
            
            melon.show_alert({
                message: __('Photo saved offline - will sync when online'),
                indicator: 'orange'
            });
        });
    },

    // AR Capabilities
    setup_ar_capabilities: function() {
        if ('xr' in navigator) {
            this.check_ar_support();
        }
    },

    check_ar_support: function() {
        navigator.xr.isSessionSupported('immersive-ar')
            .then(supported => {
                this.ar_supported = supported;
                if (supported) {
                    this.setup_ar_features();
                }
            });
    },

    start_ar_measurement: function() {
        if (!this.ar_supported) {
            melon.msgprint(__('AR not supported on this device'));
            return;
        }

        // Initialize AR session
        navigator.xr.requestSession('immersive-ar', {
            requiredFeatures: ['hit-test']
        })
        .then(session => {
            this.ar_session = session;
            this.setup_ar_scene();
        })
        .catch(error => {
            melon.msgprint(__('Failed to start AR session: {0}', [error.message]));
        });
    },

    // Voice Recognition
    setup_voice_recognition: function() {
        if ('speechRecognition' in window || 'webkitSpeechRecognition' in window) {
            this.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.speech_enabled = true;
        }
    },

    start_voice_input: function() {
        if (!this.speech_enabled) {
            melon.msgprint(__('Voice recognition not supported'));
            return;
        }

        const recognition = new this.SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = melon.boot.lang || 'en-US';

        recognition.onstart = () => {
            melon.show_alert({
                message: __('Voice recognition started. Speak now...'),
                indicator: 'blue'
            });
        };

        recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    transcript += event.results[i][0].transcript;
                }
            }
            
            if (transcript) {
                this.process_voice_command(transcript);
            }
        };

        recognition.start();
        
        // Auto-stop after 30 seconds
        setTimeout(() => {
            recognition.stop();
        }, 30000);
    },

    process_voice_command: function(transcript) {
        const command = transcript.toLowerCase();
        
        // Parse voice commands
        if (command.includes('save')) {
            if (cur_frm) cur_frm.save();
        } else if (command.includes('new valuation')) {
            melon.new_doc('Valuation');
        } else if (command.includes('new boq')) {
            melon.new_doc('BOQ');
        } else {
            // General text input to focused field
            const active_field = $('.input-with-feedback:focus');
            if (active_field.length > 0) {
                active_field.val(transcript);
                active_field.trigger('change');
            }
        }
        
        melon.show_alert({
            message: __('Voice command: {0}', [transcript]),
            indicator: 'blue'
        });
    },

    // Barcode Scanner
    setup_barcode_scanner: function() {
        if ('BarcodeDetector' in window) {
            this.barcode_detector = new BarcodeDetector();
            this.barcode_enabled = true;
        }
    },

    scan_barcode: function() {
        if (!this.barcode_enabled) {
            melon.msgprint(__('Barcode scanning not supported on this device'));
            return;
        }

        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        .then(stream => {
            this.show_barcode_scanner(stream);
        })
        .catch(error => {
            melon.msgprint(__('Camera access denied for barcode scanning'));
        });
    },

    // Offline data management
    sync_offline_data: function(silent = false) {
        if (!silent) {
            melon.show_alert({
                message: __('Syncing offline data...'),
                indicator: 'blue'
            });
        }

        this.get_offline_data().then(data => {
            if (data.length > 0) {
                this.upload_offline_data(data, silent);
            } else if (!silent) {
                melon.show_alert({
                    message: __('No offline data to sync'),
                    indicator: 'green'
                });
            }
        });
    },

    get_offline_data: function() {
        return new Promise((resolve) => {
            const request = indexedDB.open('QuantitySurveyDB', 2);

            request.onupgradeneeded = function(event) {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('offlineData')) {
                    const store = db.createObjectStore('offlineData', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('doctype', 'doctype', { unique: false });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                }
                if (!db.objectStoreNames.contains('attachments')) {
                    const attachStore = db.createObjectStore('attachments', { keyPath: 'id', autoIncrement: true });
                    attachStore.createIndex('filename', 'filename', { unique: false });
                }
            };

            request.onsuccess = function(event) {
                const db = event.target.result;
                const transaction = db.transaction(['offlineData'], 'readonly');
                const store = transaction.objectStore('offlineData');
                const getRequest = store.getAll();

                getRequest.onsuccess = function() {
                    resolve(getRequest.result || []);
                };
            };

            request.onerror = function() {
                resolve([]);
            };
        });
    }
};

// Initialize mobile functionality
$(document).ready(function() {
    quantity_survey.mobile.init();
    
    // Set current camera to back camera initially
    quantity_survey.mobile.current_camera = 'environment';
    quantity_survey.mobile.flash_on = false;
});
