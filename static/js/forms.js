document.addEventListener('DOMContentLoaded', function() {
    // Validação de formulários
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Máscara para campos monetários
    const moneyInputs = document.querySelectorAll('.money');
    moneyInputs.forEach(input => {
        IMask(input, {
            mask: 'R$ num',
            blocks: {
                num: {
                    mask: Number,
                    thousandsSeparator: '.',
                    radix: ',',
                    scale: 2,
                    padFractionalZeros: true,
                    normalizeZeros: true,
                    min: 0
                }
            }
        });
    });
}); 