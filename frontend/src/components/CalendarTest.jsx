import React from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import resourceTimelinePlugin from '@fullcalendar/resource-timeline'
import resourceDayGridPlugin from '@fullcalendar/resource-daygrid'

const CalendarTest = () => {
  const events = [
    {
      id: '1',
      title: 'Test Event',
      start: '2024-01-15',
      end: '2024-01-17',
      backgroundColor: '#3B82F6',
      borderColor: '#3B82F6',
      textColor: '#FFFFFF'
    }
  ]

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Test de FullCalendar con Plugins</h2>
      <div className="bg-white rounded-lg shadow-lg p-4">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, resourceTimelinePlugin, resourceDayGridPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,resourceTimelineWeek'
          }}
          events={events}
          editable={true}
          droppable={true}
          resizable={true}
          height="auto"
          buttonText={{
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día',
            resourceTimelineWeek: 'Habitaciones'
          }}
        />
      </div>
    </div>
  )
}

export default CalendarTest

