// background.js

// Store blocked tabs with their state
const blockedTabs = new Map();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!sender.tab || !sender.tab.id) return;
  const tabId = sender.tab.id;

  if (msg.action === 'check-blocked-status') {
    // Content script asking if this tab should be blocked
    const isBlocked = blockedTabs.has(tabId);
    sendResponse({ isBlocked });
    return true; // Keep message channel open
  }

  if (msg.action === 'set-blocked-status') {
    if (msg.blocked) {
      // Set tab as blocked with timeout
      const timeoutId = setTimeout(() => {
        blockedTabs.delete(tabId);
        // Notify content script that blocking period is over
        chrome.tabs.sendMessage(tabId, { action: 'unblock' }).catch(() => {});
      }, msg.delayMs);
      
      blockedTabs.set(tabId, {
        timeoutId,
        startTime: Date.now(),
        delayMs: msg.delayMs
      });
    } else {
      // Remove blocking
      const blockInfo = blockedTabs.get(tabId);
      if (blockInfo) {
        clearTimeout(blockInfo.timeoutId);
        blockedTabs.delete(tabId);
      }
    }
  }

  if (msg.action === 'close-tab') {
    console.log('Received close-tab message for tab:', tabId);
    chrome.tabs.remove(tabId).catch((error) => {
      console.log('Error closing tab:', error);
    });
    const blockInfo = blockedTabs.get(tabId);
    if (blockInfo) {
      clearTimeout(blockInfo.timeoutId);
      blockedTabs.delete(tabId);
      console.log('Cleaned up blocked tab:', tabId);
    }
  }
});

// Clean up when tab switches away from blocked tab
chrome.tabs.onActivated.addListener(activeInfo => {
  console.log('Tab activated:', activeInfo.tabId);
  // Close ANY blocked tab when user switches to a different tab
  for (const [tabId, blockInfo] of blockedTabs.entries()) {
    console.log('Checking blocked tab:', tabId, 'vs active:', activeInfo.tabId);
    if (tabId !== activeInfo.tabId) {
      console.log('Closing blocked tab:', tabId);
      // Close the blocked tab since user switched away
      chrome.tabs.remove(tabId).catch((error) => {
        console.log('Error removing tab:', error);
      });
      clearTimeout(blockInfo.timeoutId);
      blockedTabs.delete(tabId);
    }
  }
});

// Also listen for window focus changes
chrome.windows.onFocusChanged.addListener(windowId => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    // User switched to a different application
    return;
  }
  
  // Get the active tab in the focused window
  chrome.tabs.query({ active: true, windowId: windowId }, (tabs) => {
    if (tabs.length > 0) {
      const activeTabId = tabs[0].id;
      console.log('Window focus changed, active tab:', activeTabId);
      
      // Close any blocked tabs that aren't the active tab
      for (const [tabId, blockInfo] of blockedTabs.entries()) {
        if (tabId !== activeTabId) {
          console.log('Closing blocked tab due to window focus:', tabId);
          chrome.tabs.remove(tabId).catch(() => {});
          clearTimeout(blockInfo.timeoutId);
          blockedTabs.delete(tabId);
        }
      }
    }
  });
});

// Clean up when tab is closed
chrome.tabs.onRemoved.addListener(tabId => {
  const blockInfo = blockedTabs.get(tabId);
  if (blockInfo) {
    clearTimeout(blockInfo.timeoutId);
    blockedTabs.delete(tabId);
  }
});