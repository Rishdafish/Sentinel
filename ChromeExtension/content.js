(() => {
    const OVERLAY_ID = 'focusblocker-overlay';
    let isBlocked = false;
    let canNavigate = false;
    let hasCheckedInitialUrl = false;
    
    // ───────────────────────────────────────────────────────────
    // Overlay management
    // ───────────────────────────────────────────────────────────
    function createOverlay() {
      let overlay = document.getElementById(OVERLAY_ID);
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = OVERLAY_ID;
        Object.assign(overlay.style, {
          position: 'fixed',
          top: '0',
          left: '0',
          width: '100vw',
          height: '100vh',
          background: 'black',
          zIndex: '999999',
          pointerEvents: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '18px',
          fontFamily: 'Arial, sans-serif'
        });
        document.body.appendChild(overlay);
      }
      return overlay;
    }
    
    function removeOverlay() {
      const overlay = document.getElementById(OVERLAY_ID);
      if (overlay) {
        overlay.remove();
      }
    }
    
    function showLoadingOverlay() {
      const overlay = createOverlay();
      overlay.innerHTML = 'Checking website...';
      overlay.style.background = 'rgba(0, 0, 0, 0.8)';
    }
    
    function showBlockedOverlay(seconds) {
      const overlay = createOverlay();
      overlay.innerHTML = `
        <div style="text-align: center;">
          <div>This website is blocked for focus.</div>
          <div style="margin-top: 10px;">Time remaining: <span id="countdown">${seconds}</span> seconds</div>
          <div style="margin-top: 10px; font-size: 14px;">Click anywhere to close this tab</div>
        </div>
      `;
      overlay.style.background = 'black';
      
      // Update countdown
      const countdownEl = document.getElementById('countdown');
      const countdownInterval = setInterval(() => {
        seconds--;
        if (countdownEl) {
          countdownEl.textContent = seconds;
        }
        if (seconds <= 0) {
          clearInterval(countdownInterval);
        }
      }, 1000);
      
      // Add click handler to close tab during blocked period
      overlay.addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'close-tab' });
      }, { once: true });
    }
    
    // ───────────────────────────────────────────────────────────
    // Tab switching detection - close tab if user switches away
    // ───────────────────────────────────────────────────────────
    function setupTabSwitchDetection() {
      // Close tab if user switches away during any part of the blocking period
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && isBlocked) {
          chrome.runtime.sendMessage({ action: 'close-tab' });
        }
      });
    }
    
    // ───────────────────────────────────────────────────────────
    // Server communication
    // ───────────────────────────────────────────────────────────
    function checkWithServer(url) {
      showLoadingOverlay();
      
      return fetch('http://127.0.0.1:5000/api/ChromeExt/checkWebsite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ website: url })
      })
      .then(response => response.text())
      .then(text => {
        const serverBlocked = text.trim().toLowerCase() === 'false';
        return serverBlocked;
      })
      .catch(error => {
        console.error('FocusBlocker server error:', error);
        removeOverlay();
        return false; // Default to not blocked if server error
      });
    }
    
    // ───────────────────────────────────────────────────────────
    // Main blocking logic
    // ───────────────────────────────────────────────────────────
    function handleBlockingResult(shouldBlock) {
      if (shouldBlock) {
        isBlocked = true;
        canNavigate = false;
        
        const delaySeconds = Math.floor(Math.random() * 21) + 10; // 10-30 seconds
        const delayMs = delaySeconds * 1000;
        
        // Tell background script about blocking status
        chrome.runtime.sendMessage({
          action: 'set-blocked-status',
          blocked: true,
          delayMs: delayMs
        });
        
        showBlockedOverlay(delaySeconds);
        
        // After 3 seconds, allow navigation within the site but keep overlay
        setTimeout(() => {
          canNavigate = true;
          // Update overlay to show that navigation is allowed within this site
          const overlay = document.getElementById(OVERLAY_ID);
          if (overlay) {
            const countdownDiv = overlay.querySelector('#countdown').parentElement;
            const clickDiv = overlay.querySelector('div:last-child');
            if (clickDiv) {
              clickDiv.innerHTML = 'You can now navigate within this site, but switching tabs will close this tab';
            }
          }
        }, 3000);
        
        // Remove overlay after full delay
        setTimeout(() => {
          removeOverlay();
          isBlocked = false;
          chrome.runtime.sendMessage({
            action: 'set-blocked-status',
            blocked: false
          });
        }, delayMs);
        
      } else {
        // Not blocked - remove overlay and allow normal browsing
        removeOverlay();
        isBlocked = false;
        chrome.runtime.sendMessage({
          action: 'set-blocked-status',
          blocked: false
        });
      }
    }
    
    // ───────────────────────────────────────────────────────────
    // URL change detection
    // ───────────────────────────────────────────────────────────
    let lastUrl = location.href;
    
    function checkCurrentUrl() {
      // Don't re-check if we're already blocked and can navigate
      if (isBlocked && canNavigate) {
        return;
      }
      
      checkWithServer(location.href)
        .then(shouldBlock => {
          handleBlockingResult(shouldBlock);
        });
    }
    
    // ───────────────────────────────────────────────────────────
    // Listen for messages from background script
    // ───────────────────────────────────────────────────────────
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.action === 'unblock') {
        removeOverlay();
        isBlocked = false;
        canNavigate = true;
      }
    });
    
    // ───────────────────────────────────────────────────────────
    // Initialize
    // ───────────────────────────────────────────────────────────
    function init() {
      // Check if this tab was already blocked (in case of page refresh)
      chrome.runtime.sendMessage({ action: 'check-blocked-status' }, response => {
        if (response && response.isBlocked) {
          isBlocked = true;
          canNavigate = false;
          showBlockedOverlay(10); // Show generic blocked overlay
        } else {
          // New page load - check with server
          checkCurrentUrl();
        }
      });
      
      setupTabSwitchDetection();
      hasCheckedInitialUrl = true;
    }
    
    // ───────────────────────────────────────────────────────────
    // URL change monitoring for SPA navigation
    // ───────────────────────────────────────────────────────────
    const observer = new MutationObserver(() => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        
        // Only check new URLs if we're not in a blocked state or if we can navigate
        if (!isBlocked || canNavigate) {
          checkCurrentUrl();
        }
      }
    });
    
    // Start observing after initial check
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        observer.observe(document, { subtree: true, childList: true });
        init();
      });
    } else {
      observer.observe(document, { subtree: true, childList: true });
      init();
    }
    
    console.log('✅ FocusBlocker content script initialized');
})();