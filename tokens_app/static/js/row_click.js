document.addEventListener('DOMContentLoaded', function () {
      const rows = document.querySelectorAll('#dataTable tbody tr');
      const form = document.getElementById('tokenForm');

      const cards = document.querySelectorAll('.card-clickable');

      cards.forEach(card => {
        card.addEventListener('click', function() {
          cards.forEach(c => c.classList.remove('border-warning'));
          this.classList.add('border-warning');
          const samaccountname = this.getAttribute('data-samaccountname');
          form.label.value = samaccountname;

        });
      });


      rows.forEach(row => {
        row.addEventListener('click', function () {
          // Снимаем выделение
          rows.forEach(r => r.classList.remove('table-active'));
          // Выделяем текущую
          this.classList.add('table-active');


          // Получаем данные
          const model = this.getAttribute('data-model');
          const sn_raw = this.getAttribute('data-sn-raw');
          const sn = this.getAttribute('data-sn');
          const min_pin = this.getAttribute('data-min-pin');
          const label = this.getAttribute('data-label');

          // Заполняем форму
          form.model.value = model;
          form.serial_num_raw.value = sn_raw;
          form.serial_num.value = sn;
          form.min_pin_user.value = min_pin;
          form.label.value = label;
        });
      });
    });