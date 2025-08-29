// Quantity Survey Service Worker for Offline Capabilities
// Provides offline sync and caching for mobile users

const CACHE_NAME = 'quantity-survey-v1';
const urlsToCache = [
  '/app/quantity-survey',
  '/assets/quantity_survey/css/quantity_survey.css',
  '/assets/quantity_survey/js/quantity_survey.js',
  '/assets/quantity_survey/css/mobile.css',
  '/assets/quantity_survey/js/mobile.js'
];

// Install Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch Event - Serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Background Sync for offline data
self.addEventListener('sync', event => {
  if (event.tag === 'final-account-sync') {
    event.waitUntil(syncFinalAccountData());
  }
  
  if (event.tag === 'valuation-sync') {
    event.waitUntil(syncValuationData());
  }
});

async function syncFinalAccountData() {
  try {
    const offlineData = await getOfflineData('final-account');
    
    for (const data of offlineData) {
      await fetch('/api/method/quantity_survey.api.sync_offline_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doctype: 'Final Account',
          data: data
        })
      });
    }
    
    // Clear synced data
    await clearOfflineData('final-account');
    
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

async function syncValuationData() {
  try {
    const offlineData = await getOfflineData('valuation');
    
    for (const data of offlineData) {
      await fetch('/api/method/quantity_survey.api.sync_offline_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doctype: 'Valuation',
          data: data
        })
      });
    }
    
    await clearOfflineData('valuation');
    
  } catch (error) {
    console.error('Valuation sync failed:', error);
  }
}

async function getOfflineData(type) {
  return new Promise((resolve) => {
    const request = indexedDB.open('QuantitySurveyDB', 1);
    
    request.onsuccess = function(event) {
      const db = event.target.result;
      const transaction = db.transaction(['offlineData'], 'readonly');
      const store = transaction.objectStore('offlineData');
      const getRequest = store.getAll();
      
      getRequest.onsuccess = function() {
        const allData = getRequest.result || [];
        const filteredData = allData.filter(item => item.type === type);
        resolve(filteredData);
      };
    };
    
    request.onerror = function() {
      resolve([]);
    };
  });
}

async function clearOfflineData(type) {
  return new Promise((resolve) => {
    const request = indexedDB.open('QuantitySurveyDB', 1);
    
    request.onsuccess = function(event) {
      const db = event.target.result;
      const transaction = db.transaction(['offlineData'], 'readwrite');
      const store = transaction.objectStore('offlineData');
      
      // Get all data and delete items of specified type
      const getAllRequest = store.getAll();
      getAllRequest.onsuccess = function() {
        const allData = getAllRequest.result || [];
        allData.forEach(item => {
          if (item.type === type) {
            store.delete(item.id);
          }
        });
        resolve();
      };
    };
  });
}

// Push notifications for important updates
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New quantity survey update',
    icon: '/assets/quantity_survey/images/icon-192x192.png',
    badge: '/assets/quantity_survey/images/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/assets/quantity_survey/images/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/assets/quantity_survey/images/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Quantity Survey', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'explore') {
    // Open the app
    event.waitUntil(
      clients.openWindow('/app/quantity-survey')
    );
  }
});
