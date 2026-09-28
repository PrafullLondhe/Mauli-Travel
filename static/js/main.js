// =========================================================
// 3. INTERACTIVE AVAILABILITY CALENDAR
// =========================================================
const calendarDaysContainer = document.getElementById('calendarDays');
const monthYearLabel = document.getElementById('monthYear');
const prevMonthBtn = document.getElementById('prevMonth');
const nextMonthBtn = document.getElementById('nextMonth');
const travelDateInput = document.getElementById('travel_date');

if (calendarDaysContainer && monthYearLabel) {

  let currentDate = new Date();
  let acceptedDates = [];

  function renderCalendar(date) {

    calendarDaysContainer.innerHTML = '';

    const year = date.getFullYear();
    const month = date.getMonth();

    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December'
    ];

    monthYearLabel.textContent =
      `${monthNames[month]} ${year}`;

    // First day of month
    const firstDayIndex =
      new Date(year, month, 1).getDay();

    // Number of days in month
    const totalDays =
      new Date(year, month + 1, 0).getDate();

    // Empty boxes before first day
    for (let i = 0; i < firstDayIndex; i++) {

      const emptySlot = document.createElement('div');

      emptySlot.className = 'cal-day empty';

      calendarDaysContainer.appendChild(emptySlot);
    }

    // Actual calendar dates
    for (let day = 1; day <= totalDays; day++) {

      const daySlot = document.createElement('div');

      daySlot.className = 'cal-day';

      daySlot.textContent = day;

      const formattedMonth =
        String(month + 1).padStart(2, '0');

      const formattedDay =
        String(day).padStart(2, '0');

      const dateString =
        `${year}-${formattedMonth}-${formattedDay}`;

      // BOOKED DATE
      if (acceptedDates.includes(dateString)) {

        daySlot.classList.add('booked');

        daySlot.title = 'Date Booked / Accepted';

      }

      // AVAILABLE DATE
      else {

        daySlot.classList.add('available');

        daySlot.title = 'Available';

        daySlot.addEventListener('click', () => {

          if (travelDateInput) {
            travelDateInput.value = dateString;
          }

          const bookingForm =
            document.getElementById('bookingForm');

          if (bookingForm) {

            bookingForm.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });

          }

        });

      }

      calendarDaysContainer.appendChild(daySlot);
    }
  }

  // IMPORTANT:
  // Render calendar immediately
  renderCalendar(currentDate);


  // Previous month
  if (prevMonthBtn) {

    prevMonthBtn.addEventListener('click', () => {

      currentDate.setMonth(
        currentDate.getMonth() - 1
      );

      renderCalendar(currentDate);

    });

  }


  // Next month
  if (nextMonthBtn) {

    nextMonthBtn.addEventListener('click', () => {

      currentDate.setMonth(
        currentDate.getMonth() + 1
      );

      renderCalendar(currentDate);

    });

  }


  // Get booked dates from Flask
  fetch('/api/calendar-events')

    .then(response => {

      if (!response.ok) {
        throw new Error('Calendar API error');
      }

      return response.json();

    })

    .then(data => {

      if (
        data &&
        Array.isArray(data.accepted_dates)
      ) {

        acceptedDates = data.accepted_dates;

        renderCalendar(currentDate);

      }

    })

    .catch(error => {

      console.warn(
        'Could not load booked dates:',
        error
      );

      // Keep normal calendar visible
      renderCalendar(currentDate);

    });

}