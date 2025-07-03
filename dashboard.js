   pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.worker.min.js';

    let currentDocId = null; 
    let documentsData = []; 
    let documentPlaceholders = {}; 
    
    let currentPdf = null, currentPage = 1, totalPages = 1, pdfScale = 1.5;
    let placeholders = [];
    let isAddingPlaceholder = false;
    let isDragging = false, dragOffsetX = 0, dragOffsetY = 0;

    const pdfModal = new bootstrap.Modal(document.getElementById('pdfModal'));
    const sendLinkModal = new bootstrap.Modal(document.getElementById('sendLinkModal')); 
    const pdfContainer = document.getElementById('pdf-container');
    const pdfViewer = document.getElementById('pdf-viewer');
    const pageInfo = document.getElementById('pageInfo');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const addSignatureBtn = document.getElementById('addSignature');
    const saveDocumentBtn = document.getElementById('saveDocument');
    
    function getStatusBadge(status) { 
      const lower = status.toLowerCase(); 
      if (lower.includes('pending')) return 'status-badge status-pending'; 
      if (lower.includes('complete')) return 'status-badge status-completed'; 
      if (lower.includes('fail') || lower.includes('error')) return 'status-badge status-failed'; 
      return 'status-badge'; 
    }
    
    function getFileIcon(filename) { 
      const extension = filename.split('.').pop().toLowerCase(); 
      const icons = { 
        pdf: 'file-earmark-pdf-fill', 
        doc: 'file-earmark-word-fill', 
        docx: 'file-earmark-word-fill', 
        xls: 'file-earmark-excel-fill', 
        xlsx: 'file-earmark-excel-fill', 
        ppt: 'file-earmark-ppt-fill', 
        pptx: 'file-earmark-ppt-fill', 
        txt: 'file-earmark-text-fill', 
        jpg: 'file-earmark-image-fill', 
        jpeg: 'file-earmark-image-fill', 
        png: 'file-earmark-image-fill', 
        gif: 'file-earmark-image-fill' 
      }; 
      return icons[extension] || 'file-earmark-fill'; 
    }

    function viewDocument(url, docId) {
      currentDocId = docId;
      placeholders = documentPlaceholders[docId] ? JSON.parse(JSON.stringify(documentPlaceholders[docId])) : [];
      currentPdf = null;
      currentPage = 1;
      resetAddMode();
      
      // Show loading state with animation
      pdfViewer.innerHTML = `
        <div class="d-flex flex-column justify-content-center align-items-center h-100 mt-5">
          <div class="spinner mb-3"></div>
          <p class="text-muted">Loading document...</p>
        </div>`;
      
      pdfModal.show();
      
      pdfjsLib.getDocument(url).promise.then(pdf => {
        currentPdf = pdf;
        totalPages = pdf.numPages;
        renderPage(currentPage);
      }).catch(error => {
        console.error('Error loading PDF:', error);
        pdfViewer.innerHTML = `
          <div class="alert alert-danger m-4">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            Failed to load PDF document. Please try again.
          </div>`;
      });
    }

    async function renderPage(pageNum) { 
      if (!currentPdf) return; 
      currentPage = pageNum; 
      pdfViewer.innerHTML = ''; 
      try { 
        const page = await currentPdf.getPage(pageNum); 
        const viewport = page.getViewport({ scale: pdfScale }); 
        const canvas = document.createElement('canvas'); 
        canvas.getContext('2d'); 
        canvas.height = viewport.height; 
        canvas.width = viewport.width; 
        
        const canvasContainer = document.createElement('div'); 
        canvasContainer.className = 'canvas-container'; 
        canvasContainer.style.width = `${viewport.width}px`; 
        canvasContainer.style.height = `${viewport.height}px`; 
        canvasContainer.appendChild(canvas); 
        pdfViewer.appendChild(canvasContainer); 
        
        await page.render({ 
          canvasContext: canvas.getContext('2d'), 
          viewport: viewport 
        }).promise; 
        
        renderPlaceholdersForCurrentPage(); 
        setupPlaceholderInteraction(canvasContainer); 
      } catch (error) { 
        console.error('Error rendering page:', error); 
        pdfViewer.innerHTML = `
          <div class="alert alert-danger m-4">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            Failed to render PDF page.
          </div>`; 
      } finally { 
        updatePageInfo(); 
      } 
    }
    
    function renderPlaceholdersForCurrentPage() { 
      const canvasContainer = pdfViewer.querySelector('.canvas-container'); 
      if (!canvasContainer) return; 
      
      // Remove existing placeholders
      canvasContainer.querySelectorAll('.signature-placeholder').forEach(el => el.remove()); 
      
      const viewport = { 
        width: canvasContainer.offsetWidth, 
        height: canvasContainer.offsetHeight 
      }; 
      
      // Filter placeholders for current page and render them
      placeholders
        .filter(p => p.page === currentPage)
        .forEach(placeholderData => { 
          const placeholderEl = createPlaceholderElement(placeholderData, viewport); 
          canvasContainer.appendChild(placeholderEl); 
        }); 
    }
    
    function createPlaceholderElement(placeholderData, viewport) {
        const el = document.createElement('div');
        el.className = 'signature-placeholder';
        el.dataset.id = placeholderData.id;
        el.style.left = `${placeholderData.x * viewport.width}px`;
        el.style.top = `${placeholderData.y * viewport.height}px`;
        el.style.width = `${placeholderData.width * viewport.width}px`;
        el.style.height = `${placeholderData.width * viewport.width}px`; // Force square shape
        el.innerHTML = `
            <span>${placeholderData.type}</span>
            <div class="placeholder-controls" data-action="delete">
              <i class="bi bi-x-lg"></i>
            </div>`;
        return el;
    }

    function setupPlaceholderInteraction(canvasContainer) {
        // Click handler for adding new placeholders
        canvasContainer.addEventListener('click', e => {
            if (!isAddingPlaceholder || e.target.closest('.signature-placeholder')) return;
            
            const rect = canvasContainer.getBoundingClientRect();
            const viewport = { width: rect.width, height: rect.height };
            
            // Set square dimensions (120px x 120px)
            const placeholderSizePx = 120;
            
            const newPlaceholder = { 
                id: Date.now().toString(), 
                page: currentPage, 
                type: 'Signature', 
                x: (e.clientX - rect.left - (placeholderSizePx / 2)) / viewport.width, 
                y: (e.clientY - rect.top - (placeholderSizePx / 2)) / viewport.height, 
                width: placeholderSizePx / viewport.width, 
                height: placeholderSizePx / viewport.width // Force square shape
            };
            
            placeholders.push(newPlaceholder);
            renderPlaceholdersForCurrentPage();
            resetAddMode();
            
            // Show success feedback
            const feedback = document.createElement('div');
            feedback.className = 'position-fixed bg-success text-white px-3 py-2 rounded';
            feedback.style.left = `${e.clientX}px`;
            feedback.style.top = `${e.clientY - 40}px`;
            feedback.style.zIndex = '9999';
            feedback.innerHTML = '<i class="bi bi-check-circle me-2"></i>Signature field added';
            document.body.appendChild(feedback);
            
            setTimeout(() => {
                feedback.style.opacity = '0';
                feedback.style.transform = 'translateY(-10px)';
                setTimeout(() => feedback.remove(), 300);
            }, 1000);
        });

        // Mouse down handler for existing placeholders
        canvasContainer.addEventListener('mousedown', e => {
            const placeholderEl = e.target.closest('.signature-placeholder');
            if (!placeholderEl) return;
            
            const isDeleteButton = e.target.closest('[data-action="delete"]');

            if (isDeleteButton) {
                e.preventDefault();
                const id = placeholderEl.dataset.id;
                placeholders = placeholders.filter(p => p.id !== id);
                
                // Add fade-out animation before removing
                placeholderEl.style.opacity = '0';
                placeholderEl.style.transform = 'scale(0.9)';
                setTimeout(() => placeholderEl.remove(), 200);
                return;
            }
            
            // Only allow dragging (no resizing)
            e.preventDefault();
            isDragging = true;
            resetAddMode();
            pdfContainer.style.cursor = 'grabbing';
            
            const rect = placeholderEl.getBoundingClientRect();
            dragOffsetX = e.clientX - rect.left;
            dragOffsetY = e.clientY - rect.top;
            
            placeholderEl.classList.add('dragging');
            document.addEventListener('mousemove', handleDrag);
            document.addEventListener('mouseup', stopDrag);
        });
    }

    function handleDrag(e) { 
        if (!isDragging) return; 
        const placeholderEl = document.querySelector('.signature-placeholder.dragging'); 
        const canvasContainer = pdfViewer.querySelector('.canvas-container'); 
        if (!placeholderEl || !canvasContainer) return; 
        
        const containerRect = canvasContainer.getBoundingClientRect(); 
        let newX = e.clientX - containerRect.left - dragOffsetX; 
        let newY = e.clientY - containerRect.top - dragOffsetY; 
        
        // Constrain to container bounds
        newX = Math.max(0, Math.min(newX, containerRect.width - placeholderEl.offsetWidth)); 
        newY = Math.max(0, Math.min(newY, containerRect.height - placeholderEl.offsetHeight)); 
        
        placeholderEl.style.left = `${newX}px`; 
        placeholderEl.style.top = `${newY}px`; 
    }
    
    function stopDrag() { 
        if (!isDragging) return; 
        isDragging = false; 
        pdfContainer.style.cursor = 'default'; 
        
        const placeholderEl = document.querySelector('.signature-placeholder.dragging'); 
        const canvasContainer = pdfViewer.querySelector('.canvas-container'); 
        
        if (placeholderEl && canvasContainer) { 
            const containerRect = canvasContainer.getBoundingClientRect(); 
            const id = placeholderEl.dataset.id; 
            const placeholderData = placeholders.find(p => p.id === id); 
            
            if (placeholderData) { 
                // Update position in our data model
                placeholderData.x = parseFloat(placeholderEl.style.left) / containerRect.width; 
                placeholderData.y = parseFloat(placeholderEl.style.top) / containerRect.height; 
            } 
            
            placeholderEl.classList.remove('dragging');
        } 
        
        document.removeEventListener('mousemove', handleDrag); 
        document.removeEventListener('mouseup', stopDrag); 
    }

    function updatePageInfo() { 
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`; 
        prevPageBtn.disabled = currentPage <= 1; 
        nextPageBtn.disabled = currentPage >= totalPages; 
    }
    
    function resetAddMode() { 
        isAddingPlaceholder = false; 
        pdfContainer.style.cursor = 'default'; 
        addSignatureBtn.classList.remove('btn-primary'); 
        addSignatureBtn.classList.add('btn-outline-primary'); 
    }

    // Event listeners for page navigation
    prevPageBtn.addEventListener('click', () => { 
        if (currentPage > 1) renderPage(currentPage - 1); 
    });
    
    nextPageBtn.addEventListener('click', () => { 
        if (currentPage < totalPages) renderPage(currentPage + 1); 
    });
    
    // Toggle add signature mode
    addSignatureBtn.addEventListener('click', function() { 
        isAddingPlaceholder = !isAddingPlaceholder; 
        this.classList.toggle('btn-primary'); 
        this.classList.toggle('btn-outline-primary'); 
        pdfContainer.style.cursor = isAddingPlaceholder ? 'crosshair' : 'default'; 
        
        if (isAddingPlaceholder) {
            // Show tooltip feedback
            const tooltip = document.createElement('div');
            tooltip.className = 'position-fixed bg-dark text-white px-3 py-2 rounded';
            tooltip.style.left = '50%';
            tooltip.style.top = '100px';
            tooltip.style.transform = 'translateX(-50%)';
            tooltip.style.zIndex = '9999';
            tooltip.innerHTML = '<i class="bi bi-mouse me-2"></i>Click on the document to place signature field';
            document.body.appendChild(tooltip);
            
            setTimeout(() => {
                tooltip.style.opacity = '0';
                setTimeout(() => tooltip.remove(), 300);
            }, 3000);
        }
    });
    
    // Save document handler
    saveDocumentBtn.addEventListener('click', () => {
        if (placeholders.length === 0) {
            // Show error feedback
            const alert = document.createElement('div');
            alert.className = 'position-fixed bg-danger text-white px-3 py-2 rounded';
            alert.style.left = '50%';
            alert.style.top = '100px';
            alert.style.transform = 'translateX(-50%)';
            alert.style.zIndex = '9999';
            alert.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Please add at least one signature field';
            document.body.appendChild(alert);
            
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 3000);
            return;
        }
        
        // Save placeholders for this document
        documentPlaceholders[currentDocId] = JSON.parse(JSON.stringify(placeholders));
        
        // Show success feedback
        saveDocumentBtn.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Saved!';
        saveDocumentBtn.classList.add('btn-success');
        saveDocumentBtn.classList.remove('btn-primary');
        
        setTimeout(() => {
            showSendLinkModal(currentDocId);
            pdfModal.hide();
            
            // Reset button state
            setTimeout(() => {
                saveDocumentBtn.innerHTML = '<i class="bi bi-send-fill me-2"></i> Save & Get Link';
                saveDocumentBtn.classList.remove('btn-success');
                saveDocumentBtn.classList.add('btn-primary');
            }, 500);
        }, 1000);
    });
    
    function showSendLinkModal(docId) {
        const doc = documentsData.find(d => d.id === docId);
        const placeholdersForDoc = documentPlaceholders[docId];
        
        if (!doc || !placeholdersForDoc || placeholdersForDoc.length === 0) {
            alert('Error: Placeholders not found. Please prepare the document first.');
            return;
        }
        
        const encodedPlaceholders = encodeURIComponent(JSON.stringify(placeholdersForDoc));
        const clientLink = `${window.location.origin}${window.location.pathname.replace(/[^/]*$/, '')}client.html?pdfUrl=${encodeURIComponent(doc.file_url)}&placeholders=${encodedPlaceholders}&docId=${docId}`;
        
        document.getElementById('clientLinkInput').value = clientLink;
        document.getElementById('openLinkBtn').href = clientLink;
        document.getElementById('copy-success').classList.add('d-none');
        
        sendLinkModal.show();
    }
    
    // Copy link handler
    document.getElementById('copyLinkBtn').addEventListener('click', () => {
        const linkInput = document.getElementById('clientLinkInput');
        navigator.clipboard.writeText(linkInput.value).then(() => {
            const successMsg = document.getElementById('copy-success');
            successMsg.classList.remove('d-none');
            setTimeout(() => successMsg.classList.add('d-none'), 3000);
        });
    });

    // Reset add mode when modal closes
    document.getElementById('pdfModal').addEventListener('hidden.bs.modal', () => resetAddMode());

    // Initialize document list
    function initializeDocumentList() {
        const container = document.getElementById('documentContainer');
        const emptyState = document.getElementById('emptyState');
        
        // Clear existing content
        container.innerHTML = '';
        emptyState.classList.remove('d-none');
        
        // Show loading state
        emptyState.innerHTML = `
            <div class="spinner mb-3"></div>
            <p>Loading your documents...</p>
        `;
        
        // Fetch documents from API
        fetch('http://localhost:8000/signing/documents/decrypted/')
            .then(res => res.ok ? res.json() : Promise.reject(res))
            .then(data => {
                documentsData = data; 
                
                if (!data || data.length === 0) {
                    emptyState.innerHTML = `
                        <i class="bi bi-file-earmark-plus"></i>
                        <h4 class="mt-3">No Documents Yet</h4>
                        <p class="text-muted">Get started by uploading your first document</p>
                        <button class="btn btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#uploadDocumentModal">
                            <i class="bi bi-plus-circle-fill me-2"></i>Upload Document
                        </button>
                    `;
                    return;
                }
                
                emptyState.classList.add('d-none');
                
                // Render document cards
                data.forEach(doc => {
                    const fileName = doc.file_path.split('/').pop();
                    const createdAt = new Date(doc.created_at).toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric', 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    });
                    
                    const fileExtension = fileName.split('.').pop().toUpperCase();
                    const fileIcon = getFileIcon(fileName);
                    const isReadyToSend = documentPlaceholders[doc.id] && documentPlaceholders[doc.id].length > 0;
                    
                    const card = document.createElement('div');
                    card.className = 'document-card';
                    card.innerHTML = `
                        <div class="card-header">
                            <h5 class="card-title">${doc.title}</h5>
                        </div>
                        <div class="card-body">
                            <div class="document-type">
                                <i class="bi ${fileIcon} file-icon"></i>
                                <div>
                                    <p class="mb-1 fw-semibold">${fileName}</p>
                                    <span class="file-extension">${fileExtension}</span>
                                </div>
                            </div>
                            <div class="document-meta">
                                <i class="bi bi-person"></i>
                                <span>${doc.uploaded_by}</span>
                            </div>
                            <div class="document-meta">
                                <i class="bi bi-calendar"></i>
                                <span>${createdAt}</span>
                            </div>
                        </div>
                        <div class="card-footer">
                            <span class="${getStatusBadge(doc.status)}">${doc.status}</span>
                            <div class="card-actions">
                                <button onclick="viewDocument('${doc.file_url}', ${doc.id})" class="btn-view">
                                    <i class="bi bi-pencil-square"></i> Prepare
                                </button>
                            </div>
                        </div>
                    `;
                    
                    container.appendChild(card);
                });
            })
            .catch(err => {
                console.error('Error fetching documents:', err);
                emptyState.innerHTML = `
                    <i class="bi bi-exclamation-triangle-fill text-danger"></i>
                    <h4 class="mt-3">Error Loading Documents</h4>
                    <p class="text-muted">Could not connect to the server.</p>
                    <button class="btn btn-primary mt-2" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-2"></i> Try Again
                    </button>
                `;
            });
    }

    // Upload document logic
    const uploadModalEl = document.getElementById('uploadDocumentModal');
    const uploadModal = new bootstrap.Modal(uploadModalEl);
    const uploadForm = document.getElementById('uploadForm');
    const submitUploadBtn = document.getElementById('submitUploadBtn');
    const uploadSpinner = submitUploadBtn.querySelector('.spinner-border');
    const uploadErrorAlert = document.getElementById('upload-error-alert');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            uploadSpinner.classList.remove('d-none');
            submitUploadBtn.disabled = true;
            uploadErrorAlert.classList.add('d-none');

            const formData = new FormData(this);
            const uploadUrl = 'http://localhost:8000/signing/document/send/';

            fetch(uploadUrl, {
                method: 'POST',
                body: formData
            })
            .then(async response => {
                const data = await response.json();
                if (!response.ok) throw data;
                return data;
            })
            .then(data => {
                // Show success feedback
                const successAlert = document.createElement('div');
                successAlert.className = 'position-fixed bg-success text-white px-4 py-3 rounded';
                successAlert.style.bottom = '20px';
                successAlert.style.right = '20px';
                successAlert.style.zIndex = '9999';
                successAlert.innerHTML = `
                    <i class="bi bi-check-circle-fill me-2"></i>
                    Document uploaded successfully!
                `;
                document.body.appendChild(successAlert);
                
                setTimeout(() => {
                    successAlert.style.opacity = '0';
                    setTimeout(() => successAlert.remove(), 300);
                }, 3000);
                
                uploadModal.hide();
                initializeDocumentList();
            })
            .catch(errors => {
                console.error('Upload Error:', errors);
                let errorMessages = 'An unknown error occurred. Please check the console.';
                
                if (typeof errors === 'object' && errors !== null) {
                    errorMessages = Object.entries(errors).map(([field, messages]) => {
                        const formattedField = field.charAt(0).toUpperCase() + field.slice(1).replace('_', ' ');
                        return `<strong>${formattedField}:</strong> ${Array.isArray(messages) ? messages.join(' ') : messages}`;
                    }).join('<br>');
                }
                
                uploadErrorAlert.innerHTML = errorMessages;
                uploadErrorAlert.classList.remove('d-none');
            })
            .finally(() => {
                uploadSpinner.classList.add('d-none');
                submitUploadBtn.disabled = false;
            });
        });
    }

    // Reset upload form when modal closes
    if (uploadModalEl) {
        uploadModalEl.addEventListener('hidden.bs.modal', () => {
            if(uploadForm) uploadForm.reset();
            if(uploadErrorAlert) uploadErrorAlert.classList.add('d-none');
        });
    }

    // Initialize the app when DOM is loaded
    document.addEventListener('DOMContentLoaded', initializeDocumentList);