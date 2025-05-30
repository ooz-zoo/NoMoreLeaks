// DOM Elements
const browseBtn = document.getElementById("browseBtn");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const verifyBtn = document.getElementById("verifyBtn");
const resultsSection = document.getElementById("resultsSection");
const verificationStatus = document.getElementById("verificationStatus");
const issuerInfo = document.getElementById("issuerInfo");
const claimsList = document.getElementById("claimsList");
const generateBadgeBtn = document.getElementById("generateBadgeBtn");
const badgeDisplay = document.getElementById("badgeDisplay");
const shareOptions = document.getElementById("shareOptions");
const shareLink = document.getElementById("shareLink");
const copyLinkBtn = document.getElementById("copyLinkBtn");

// Upload Area Highlight
const uploadCard = document.querySelector(".upload-card");

// Event Listeners
browseBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", handleFileSelect);

uploadCard.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadCard.classList.add("highlight");
});

uploadCard.addEventListener("dragleave", () => {
  uploadCard.classList.remove("highlight");
});

uploadCard.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadCard.classList.remove("highlight");
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    handleFileSelect({ target: fileInput });
  }
});

verifyBtn.addEventListener("click", verifyCredential);
generateBadgeBtn.addEventListener("click", generateBadge);
copyLinkBtn.addEventListener("click", copyShareLink);

// Functions
function handleFileSelect(e) {
  if (e.target.files.length) {
    const file = e.target.files[0];
    fileName.innerHTML = `<i class="fas fa-file-alt"></i><span>${file.name}</span>`;
    verifyBtn.disabled = false;
    resetVerificationUI();
  }
}

function resetVerificationUI() {
  resultsSection.querySelector(".verification-status").innerHTML = `
    <div class="status-icon">
      <i class="fas fa-hourglass-half"></i>
    </div>
    <h3>Verification Pending</h3>
    <p>Ready to verify your credential</p>
  `;
  
  issuerInfo.innerHTML = `
    <h4><i class="fas fa-building"></i> Issuer Information</h4>
    <div class="empty-state">No issuer information available</div>
  `;
  
  claimsList.innerHTML = `
    <h4><i class="fas fa-clipboard-check"></i> Verified Claims</h4>
    <div class="empty-state">No claims verified yet</div>
  `;
  
  generateBadgeBtn.disabled = true;
  shareOptions.style.display = "none";
}

async function verifyCredential() {
  if (!fileInput.files.length) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  // Show loading state
  verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
  verifyBtn.disabled = true;

  try {
    const response = await fetch("http://localhost:8000/verify-claim", {
      method: "POST",
      body: formData,
      credentials: 'include'
    });

    const data = await response.json();

    if (!response.ok) {
      showVerificationError(data.detail || "Verification failed");
      return;
    }

    if (data.status === "verified") {
      showVerificationSuccess(data);
      generateBadgeBtn.disabled = false;
    } else {
      showVerificationError(data.error || "Verification failed");
    }
  } catch (error) {
    showVerificationError("Network error: " + error.message);
  } finally {
    verifyBtn.innerHTML = '<i class="fas fa-search"></i> Verify Credential';
    verifyBtn.disabled = false;
  }
}

function showVerificationSuccess(data) {
  verificationStatus.innerHTML = `
    <div class="status-icon">
      <i class="fas fa-check-circle"></i>
    </div>
    <h3>Verification Successful!</h3>
    <p>Your credential has been verified</p>
  `;
  verificationStatus.classList.add("success");

  issuerInfo.innerHTML = `
    <h4><i class="fas fa-building"></i> Issuer Information</h4>
    <div class="issuer-details">
      <strong>Organization:</strong> ${data.issuer}
      <span class="verified-tag"><i class="fas fa-check"></i> Verified</span>
    </div>
  `;

  if (data.verified_claims?.length) {
    claimsList.innerHTML = `
      <h4><i class="fas fa-clipboard-check"></i> Verified Claims</h4>
      <div class="claims-grid">
        ${data.verified_claims.map(claim => `
          <div class="claim-item">
            <i class="fas fa-check-circle"></i>
            ${claim}
          </div>
        `).join("")}
      </div>
    `;
  }
}

function showVerificationError(message) {
  verificationStatus.innerHTML = `
    <div class="status-icon">
      <i class="fas fa-times-circle"></i>
    </div>
    <h3>Verification Failed</h3>
    <p>${message}</p>
  `;
  verificationStatus.classList.add("error");
  generateBadgeBtn.disabled = true;
}

async function generateBadge() {
  generateBadgeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
  generateBadgeBtn.disabled = true;

  try {
    const response = await fetch("http://localhost:8000/badge", {
      method: "GET",
      credentials: 'include'
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || "Failed to generate badge");
    }

    displayBadge(data);
    
    // Show share options
    shareOptions.style.display = "flex";
    shareLink.value = `https://bbd2-105-160-27-79.ngrok-free.app/verify/${data.badge_id}`;
    
  } catch (error) {
    badgeDisplay.innerHTML = `
      <div class="error-message">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Failed to generate badge: ${error.message}</p>
      </div>
    `;
  } finally {
    generateBadgeBtn.innerHTML = '<i class="fas fa-certificate"></i> Generate My Badge';
    generateBadgeBtn.disabled = false;
  }
}

function displayBadge(badgeData) {
  badgeDisplay.innerHTML = `
    <div class="badge-card">
      <div class="badge-header">
        <h3>Verified Credential Badge</h3>
        <i class="fas fa-shield-alt"></i>
      </div>
      <div class="badge-body">
        <div class="badge-field">
          <span class="field-label">Badge ID:</span>
          <span class="field-value">${badgeData.badge_id}</span>
        </div>
        <div class="badge-field">
          <span class="field-label">Name:</span>
          <span class="field-value">${badgeData.name}</span>
        </div>
        <div class="badge-field">
          <span class="field-label">Issued By:</span>
          <span class="field-value">${badgeData.issued_by}</span>
        </div>
        <div class="badge-field">
          <span class="field-label">Issued On:</span>
          <span class="field-value">${new Date(badgeData.issued_on * 1000).toLocaleDateString()}</span>
        </div>
        <div class="badge-field">
          <span class="field-label">Expires On:</span>
          <span class="field-value">${new Date(badgeData.expires_on * 1000).toLocaleDateString()}</span>
        </div>
      </div>
      <div class="badge-qr" id="badgeQr"></div>
    </div>
  `;
}

function copyShareLink() {
  shareLink.select();
  document.execCommand("copy");
  
  // Show copied feedback
  const originalText = copyLinkBtn.innerHTML;
  copyLinkBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
  setTimeout(() => {
    copyLinkBtn.innerHTML = originalText;
  }, 2000);
}