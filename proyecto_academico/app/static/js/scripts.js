// Sistema Académico - JavaScript Principal
console.log("Sistema Académico cargado");

// ==================== SISTEMA DE ALERTAS ====================

// Función para cerrar alertas individuales
function closeAlert(alertId) {
  const alert = document.getElementById(alertId);
  if (alert) {
    alert.style.animation = "slideOutUp 0.3s ease-out forwards";
    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 300);
  }
}

// Auto-cerrar SOLO los mensajes del sistema (no las tarjetas de contenido)
function initializeAlerts() {
  // Selector específico para alertas de mensajes del sistema
  const systemAlerts = document.querySelectorAll(".messages .alert");
  
  systemAlerts.forEach((alert, index) => {
    // Agregar botón de cierre si no existe
    if (!alert.querySelector('.alert-close')) {
      const closeButton = document.createElement('button');
      closeButton.type = 'button';
      closeButton.className = 'alert-close';
      closeButton.setAttribute('aria-label', 'Cerrar');
      closeButton.innerHTML = '<i class="fas fa-times"></i>';
      
      // Generar ID único si no existe
      if (!alert.id) {
        alert.id = `system-alert-${index}`;
      }
      
      closeButton.onclick = () => closeAlert(alert.id);
      alert.appendChild(closeButton);
    }
    
    // Auto-cerrar después de 5 segundos + retraso escalonado
    setTimeout(() => {
      if (alert && alert.parentNode) {
        closeAlert(alert.id);
      }
    }, 5000 + index * 500);
  });
}

// ==================== SISTEMA DE CONFIRMACIÓN ====================

function showConfirm(message, callback) {
  // Verificar si ya existe un modal de confirmación
  const existingModal = document.querySelector('.confirmation-modal');
  if (existingModal) {
    existingModal.remove();
  }

  const confirmModal = document.createElement('div');
  confirmModal.className = 'confirmation-modal';
  confirmModal.innerHTML = `
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h4><i class="fas fa-exclamation-triangle"></i> Confirmar acción</h4>
        </div>
        <div class="modal-body">
          <p>${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-danger confirm-yes">Sí, continuar</button>
          <button class="btn btn-secondary confirm-no">Cancelar</button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(confirmModal);
  
  // Event listeners para los botones
  confirmModal.querySelector('.confirm-yes').addEventListener('click', () => {
    callback();
    confirmModal.remove();
  });
  
  confirmModal.querySelector('.confirm-no').addEventListener('click', () => {
    confirmModal.remove();
  });
  
  // Cerrar al hacer clic en el overlay
  confirmModal.querySelector('.modal-overlay').addEventListener('click', (e) => {
    if (e.target === confirmModal.querySelector('.modal-overlay')) {
      confirmModal.remove();
    }
  });
  
  // Cerrar con tecla Escape
  const escapeHandler = (e) => {
    if (e.key === 'Escape') {
      confirmModal.remove();
      document.removeEventListener('keydown', escapeHandler);
    }
  };
  document.addEventListener('keydown', escapeHandler);
  
  return false;
}

// ==================== VALIDACIÓN DE FORMULARIOS ====================

function initializeFormValidation() {
  // Validación general de formularios
  document.querySelectorAll('.form-control').forEach(input => {
    input.addEventListener('input', function() {
      validateField(this);
    });
    
    input.addEventListener('blur', function() {
      validateField(this);
    });
  });

  // Validación específica para campos de calificación
  document.querySelectorAll('.grade-input').forEach(input => {
    input.addEventListener('input', function() {
      validateGradeField(this);
    });
  });
}

function validateField(field) {
  const errorContainer = document.getElementById(`${field.name}-errors`);
  
  if (field.validity.valid) {
    field.classList.add('valid');
    field.classList.remove('invalid');
    if (errorContainer) {
      errorContainer.style.display = 'none';
    }
  } else {
    field.classList.add('invalid');
    field.classList.remove('valid');
    if (errorContainer) {
      errorContainer.style.display = 'block';
    }
  }
}

function validateGradeField(field) {
  const value = parseFloat(field.value);
  const isValid = !isNaN(value) && value >= 0 && value <= 5;
  
  if (isValid) {
    field.classList.add('valid');
    field.classList.remove('invalid');
  } else {
    field.classList.add('invalid');
    field.classList.remove('valid');
  }
}

// ==================== EDICIÓN INLINE DE NOTAS ====================

function initializeInlineGradeEditing() {
  // Botones de editar
  document.querySelectorAll('.edit-grade').forEach(button => {
    button.addEventListener('click', function() {
      const gradeDisplay = this.closest('.grade-display');
      const gradeValue = gradeDisplay.querySelector('.grade-value');
      const editForm = gradeDisplay.querySelector('.grade-edit-form');
      
      if (gradeValue && editForm) {
        gradeValue.style.display = 'none';
        this.style.display = 'none';
        editForm.style.display = 'flex';
        
        // Enfocar el input
        const input = editForm.querySelector('.grade-input');
        if (input) {
          input.focus();
          input.select();
        }
      }
    });
  });

  // Botones de cancelar edición
  document.querySelectorAll('.cancel-edit').forEach(button => {
    button.addEventListener('click', function() {
      cancelGradeEdit(this);
    });
  });
  
  // Cancelar con tecla Escape
  document.querySelectorAll('.grade-edit-form .grade-input').forEach(input => {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        const cancelButton = this.parentNode.querySelector('.cancel-edit');
        if (cancelButton) {
          cancelGradeEdit(cancelButton);
        }
      }
    });
  });
}

function cancelGradeEdit(cancelButton) {
  const gradeDisplay = cancelButton.closest('.grade-display');
  const gradeValue = gradeDisplay.querySelector('.grade-value');
  const editForm = gradeDisplay.querySelector('.grade-edit-form');
  const editButton = gradeDisplay.querySelector('.edit-grade');
  
  if (gradeValue && editForm && editButton) {
    gradeValue.style.display = 'inline-block';
    editButton.style.display = 'inline-flex';
    editForm.style.display = 'none';
    
    // Restaurar valor original
    const input = editForm.querySelector('.grade-input');
    const originalValue = gradeValue.textContent.trim();
    if (input) {
      input.value = originalValue;
    }
  }
}

// ==================== LOADING STATES ====================

function initializeLoadingStates() {
  const forms = document.querySelectorAll("form");
  
  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const submitBtn = form.querySelector('button[type="submit"]');
      
      if (submitBtn && !submitBtn.classList.contains("loading")) {
        // Guardar texto original
        const originalText = submitBtn.innerHTML;
        submitBtn.setAttribute("data-original-text", originalText);
        
        // Aplicar estado de carga
        submitBtn.classList.add("loading");
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Procesando...`;
        
        // Restaurar después de un tiempo o cuando se complete
        setTimeout(() => {
          if (submitBtn.classList.contains("loading")) {
            submitBtn.classList.remove("loading");
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
          }
        }, 10000);
      }
    });
  });
}

// ==================== INICIALIZACIÓN ====================

document.addEventListener("DOMContentLoaded", function() {
  // Inicializar todos los sistemas
  initializeAlerts();
  initializeFormValidation();
  initializeInlineGradeEditing();
  initializeLoadingStates();
  
  console.log("Todos los sistemas de EduTrack inicializados correctamente");
});

// ==================== UTILIDADES ADICIONALES ====================

// Función para mostrar notificaciones temporales
function showNotification(message, type = 'info', duration = 3000) {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} notification-toast`;
  notification.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
    ${message}
    <button type="button" class="alert-close" onclick="this.parentNode.remove()">
      <i class="fas fa-times"></i>
    </button>
  `;
  
  // Añadir al body
  document.body.appendChild(notification);
  
  // Auto-remover después de la duración especificada
  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.animation = "slideOutUp 0.3s ease-out forwards";
      setTimeout(() => notification.remove(), 300);
    }
  }, duration);
}

// Función para debugging - puede ser removida en producción
function debugAlerts() {
  const systemAlerts = document.querySelectorAll(".messages .alert");
  const contentAlerts = document.querySelectorAll(".card .alert");
  
  console.log(`Sistema encontró ${systemAlerts.length} alertas de sistema y ${contentAlerts.length} alertas de contenido`);
}