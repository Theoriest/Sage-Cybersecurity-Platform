// Add the following code to your main JavaScript file

// Make event listeners passive for better scrolling performance
document.addEventListener("DOMContentLoaded", function () {
  // Find all elements that might have touchmove listeners
  const scrollableElements = document.querySelectorAll(
    ".chapter-sidebar, .scrollable-content"
  );

  // Add passive event listeners to these elements
  scrollableElements.forEach((element) => {
    // Remove existing non-passive listeners if any
    const oldTouchMove = element.ontouchmove;
    if (oldTouchMove) {
      element.removeEventListener("touchmove", oldTouchMove);
    }

    // Add passive listener
    element.addEventListener(
      "touchmove",
      function (e) {
        // Your existing touchmove logic can go here
      },
      { passive: true }
    );
  });

  // Handle dynamic elements that might be added later
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            // Element node
            const newScrollables = node.querySelectorAll(
              ".chapter-sidebar, .scrollable-content"
            );
            newScrollables.forEach((element) => {
              element.addEventListener("touchmove", function (e) {}, {
                passive: true,
              });
            });
          }
        });
      }
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
});
