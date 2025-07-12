// Google Search Cleaner - Only remove qogDvd class

function hideElements() {
    try {
      // Hide elements with class="qogDvd"
      document.querySelectorAll('.qogDvd').forEach(element => {
        element.style.display = 'none';
        console.log('Hidden element with class qogDvd');
      });
      
    } catch (error) {
      console.log('Error hiding elements:', error);
    }
  }
  
  // Wait for page load
  setTimeout(hideElements, 2000);
  
  // Run periodically 
  setInterval(hideElements, 3000);
  
  // Handle URL changes
  let currentUrl = location.href;
  setInterval(() => {
    if (currentUrl !== location.href) {
      currentUrl = location.href;
      setTimeout(hideElements, 2000);
    }
  }, 2000);
  
  console.log('Google Search Cleaner - Only targeting qogDvd elements');