/* script.js
   - Handles real API calls to the Flask backend.
   - Dynamically populates the "Insights" section.
   - Manages loading and error states.
   - Handles copy/download actions.
*/

/* ====== DOM Elements ====== */
// Use 'getElementById' for forms, buttons, and sections
const analyzeForm = document.getElementById('analyze-form');
const productInput = document.getElementById('productLink');
const analyzeBtn = document.getElementById('analyzeBtn');
const loaderOverlay = document.getElementById('loader-overlay');
const loaderStage = document.getElementById('prog-stage');
const insightsSection = document.getElementById('insights');

// Insight card elements are retrieved once on load
const simpleSummaryText = document.getElementById('simple-summary-text');
const contextualReportHtml = document.getElementById('contextual-report-html');
const copyBtn = document.getElementById('copySummary');
const downloadBtn = document.getElementById('downloadReport');
// Get the grid to show errors
const insightsGrid = document.querySelector('#insights .insights-grid');


// Initial state placeholders
simpleSummaryText.textContent = "Click 'Analyze' to generate a simple summary of the reviews.";
contextualReportHtml.innerHTML = "<p>Click 'Analyze' to generate a detailed, human-readable report.</p>";

/* ====== Primary Event Listener ====== */
analyzeForm.addEventListener('submit', (e) => {
  e.preventDefault(); // Stop form from submitting normally
  const url = productInput.value;
  // Basic URL validation
  if (!url || !url.startsWith('http')) {
    alert("Please enter a valid product URL (e.g., https://...)");
    return;
  }
  runRealAnalysis(url);
});

/**
 * Main function to run the analysis pipeline
 * @param {string} url - The product URL to analyze
 */
async function runRealAnalysis(url) {
  // 1. Show loader and update UI state
  showLoader(true, "Initializing...");

  // Clear previous results by setting placeholders
  simpleSummaryText.textContent = "Loading...";
  contextualReportHtml.innerHTML = "<p>Generating report...</p>";

  try {
    // 2. Simulate pipeline stages for better UX
    // (This is just a visual guide for the user)
    setTimeout(() => updateLoaderStage("Scraping reviews..."), 500);
    setTimeout(() => updateLoaderStage("Extracting aspects... (takes a while)"), 2000);
    setTimeout(() => updateLoaderStage("Analyzing sentiments..."), 15000);
    setTimeout(() => updateLoaderStage("Generating final reports..."), 25000);

    // 3. Make the actual API call
    const response = await fetch('/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle errors from the server (e.g., scraping, API key)
      throw new Error(data.error || 'An unknown server error occurred.');
    }

    // 4. Success! Populate the insights section
    populateInsights(data);

  } catch (error) {
    // 5. Handle errors (e.g., network failure, server crash)
    console.error("Analysis Error:", error);

    // Display error directly in the summary card
    const errorMessage = `Analysis Failed: ${error.message}`;
    simpleSummaryText.textContent = errorMessage;
    contextualReportHtml.innerHTML = `<p style="color: #d32f2f;">${errorMessage}</p>`;

   } finally {
    // 6. Hide loader regardless of success or failure
    showLoader(false);
  }
}

/**
 * Populates the insights section with data from the API
 * @param {object} data - The JSON data from the /summarize endpoint
 */

function populateInsights(data) {
  // FIX: Directly update the content of the pre-existing elements.
  simpleSummaryText.textContent = data.simple_summary || "No simple summary available.";

  // Use marked.parse() to convert Markdown to HTML for the contextual report
  contextualReportHtml.innerHTML = marked.parse(data.contextual_report || "No contextual report available.");

  // Scroll to the insights section
  insightsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Binds event listeners to dynamically created elements (copy/download buttons)
 */
function bindDynamicElements() {
    // Since the elements are static now, we bind them once on load
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          if (simpleSummaryText) {
            // Use simpleSummaryText declared globally
            navigator.clipboard.writeText(simpleSummaryText.textContent).then(() => {
              alert("Simple summary copied to clipboard!");
            }).catch(err => {
              console.error('Failed to copy text: ', err);
              alert("Failed to copy summary. Please try manually.");
            });
          }
        });
    }

    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
          if (contextualReportHtml) {
            // Use contextualReportHtml declared globally
            const report = contextualReportHtml.innerText;
            const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'Contextual_Review_Summary.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          }
        });
    }
}
// Bind buttons on initial page load
bindDynamicElements();


/* ====== UI Helper Functions ====== */

/**
 * Shows or hides the loading modal
 * @param {boolean} show - True to show, false to hide
 * @param {string} [stage='Initializing...'] - The text to display
 */
function showLoader(show, stage = 'Initializing...') {
  if (show) {
    loaderOverlay.classList.remove('hidden');
    loaderStage.textContent = stage;
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";
  } else {
    loaderOverlay.classList.add('hidden');
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze";
  }
}

/**
 * Updates the text of the loader
 * @param {string} text - The new stage text
 */
function updateLoaderStage(text) {
  loaderStage.textContent = text;
}


/* ====== Fade-in on scroll (for static sections) ====== */
const observerOptions = { root: null, rootMargin: "0px", threshold: 0.12 };
const revealCallback = (entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("in-view");
      obs.unobserve(entry.target);
    }
  });
};
const revealObserver = new IntersectionObserver(revealCallback, observerOptions);
document.querySelectorAll(".clay-card, .step, .feature, .about-card, .contact-card")
  .forEach(el => revealObserver.observe(el));

/* Add the animation styles dynamically */
const style = document.createElement('style');
style.innerHTML = `
  .clay-card, .step, .feature, .about-card, .contact-card {
    transform: translateY(20px);
    opacity: 0;
    transition: all .7s cubic-bezier(.2,.9,.2,1);
  }
  .clay-card.in-view, .step.in-view, .feature.in-view, .about-card.in-view, .contact-card.in-view {
    transform: translateY(0);
    opacity: 1;
  }
`;
document.head.appendChild(style);
