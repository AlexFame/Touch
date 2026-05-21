# Touch Sales Offer

## One-Sentence Positioning

Touch is a Telegram Mini App booking system that helps wellness massage studios
and local service businesses accept appointments, manage visits, and reduce
manual chat work.

## Problem It Solves

Many small service businesses lose time and bookings because scheduling happens
manually in chats:

- Clients ask the same questions about services, prices, and available time.
- Booking requires back-and-forth messages.
- Cancellations and rescheduling are hard to track.
- Admins forget reminders and follow-ups.
- Google Calendar, client lists, and Telegram conversations are disconnected.
- Clients want a fast mobile experience without installing another app.

Touch turns Telegram into a simple booking app: clients open the Mini App,
choose a service, pick a day and time, and manage their visits themselves.

## Core Features

- Telegram Mini App for client booking.
- Telegram bot entry point with one clear **Open** button.
- Service list with prices, durations, descriptions, and packages.
- Booking flow: service, date, time, client details, confirmation.
- Client **My bookings** screen.
- Client cancellation and reschedule flow.
- Admin-only booking controls in Telegram.
- Google Calendar availability integration.
- Automatic busy-slot protection.
- First-visit bonus support.
- Package/course options, for example 5 or 10 sessions.
- RU/UK client UI based on Telegram language.
- Russian admin bot and calendar text.
- 24-hour reminders.
- Post-visit review and follow-up flow.
- Railway production deployment.

## Pricing Packages

Prices below are example commercial packages and can be adjusted per client.

### Start

For a solo specialist who needs a clean booking flow.

Includes:

- Telegram Mini App setup.
- Telegram bot setup.
- Up to 5 services.
- Basic service descriptions and prices.
- Basic booking flow.
- **My bookings** screen.
- Cancel/reschedule support.
- Google Calendar connection.
- Railway deployment.
- Basic launch testing.

Best for:

- Solo massage therapist.
- Small wellness cabinet.
- One-location local service business.

### Business

For a growing studio that needs packages and smoother client management.

Includes everything in Start, plus:

- Up to 10 services.
- Package/course options, for example 5 and 10 sessions.
- RU/UK client text setup.
- Client reminders.
- Google review request flow.
- Admin action buttons.
- Basic client validation.
- Production deployment checklist.
- Handover documentation.

Best for:

- Massage studio with multiple offers.
- Wellness studio selling courses.
- Local service business that wants less manual admin work.

### Growth

For a business that wants a stronger branded experience and ongoing improvement.

Includes everything in Business, plus:

- Expanded service catalog.
- Custom onboarding questionnaire.
- More detailed service/package configuration.
- Improved client follow-up flow.
- Branded Mini App copy and visual polish.
- Launch support.
- Priority fixes during launch window.
- Roadmap for future improvements.

Best for:

- Studio preparing for active promotion.
- Business with multiple service categories.
- Owner who wants ongoing optimization after launch.

## Monthly Support Options

### Basic Support

- Small text and price updates.
- Monitoring of basic uptime issues.
- Minor bug fixes.
- Monthly health check.

### Standard Support

- Everything in Basic.
- Service/package updates.
- Booking rule adjustments.
- Google Calendar troubleshooting.
- Telegram/BotFather support.
- Small UX improvements.

### Priority Support

- Everything in Standard.
- Faster response time.
- Launch campaign support.
- Monthly improvement planning.
- More active monitoring of Railway, bot, and Mini App behavior.

## What Is Included

- Setup of the Telegram bot and Mini App.
- Backend API configuration.
- Railway deployment guidance/setup.
- PostgreSQL production database setup.
- Google Calendar integration when credentials are provided.
- Client-facing service setup based on approved content.
- Basic testing before launch.
- Documentation for handover and future setup.

## What Is Not Included

- Paid Telegram, Railway, Google, or third-party platform costs.
- Creating or managing the client's Google account.
- Legal/medical compliance review.
- Professional copywriting beyond agreed setup content.
- Professional brand design or illustration work unless agreed separately.
- Large custom features outside the selected package.
- Guarantee of bookings, sales volume, or advertising results.

## Client Onboarding Process

1. **Intro call**
   Understand the business, services, booking flow, and launch goals.

2. **Client intake form**
   Collect business details, services, prices, working hours, policies, language
   preferences, Telegram admin IDs, and Google Calendar details.

3. **Service configuration**
   Convert intake data into Touch services, descriptions, packages, and booking
   rules.

4. **Telegram and Google setup**
   Configure BotFather, admin access, Google Calendar access, and review URL.

5. **Railway deployment**
   Deploy Backend API, Bot Worker, Mini App, and PostgreSQL.

6. **Testing**
   Test booking, cancellation, reschedule, reminders, admin controls, language
   behavior, and Google Calendar.

7. **Launch**
   Set the production Mini App URL in BotFather and give the client final usage
   notes.

8. **Support**
   Continue with the selected monthly support option if needed.

## Simple Demo Pitch Text

Here is the simplest way to show Touch to a potential client:

```text
Touch lets your clients book a massage directly inside Telegram. They press
"Open", choose a service, pick a free time, and confirm the visit without
messaging back and forth. You get fewer repetitive chats, fewer missed details,
and a cleaner booking flow connected to your calendar.
```

Short version:

```text
It is your booking app inside Telegram: services, prices, free times,
appointments, reminders, and client self-service in one place.
```

## FAQ For Non-Technical Clients

### Do my clients need to install a new app?

No. They open the booking app inside Telegram.

### Is this a website?

It behaves like a small app inside Telegram. Technically it is a Telegram Mini
App connected to a backend and database.

### Can clients book without writing to me?

Yes. They can choose the service, day, and time themselves.

### Can I still talk to clients manually?

Yes. Touch does not replace Telegram chats. It removes repetitive scheduling
work and keeps booking information more organized.

### Can it connect to my Google Calendar?

Yes, if you provide calendar access through a Google service account. Busy
calendar time can block unavailable slots.

### Can clients cancel or reschedule?

Yes, if those options are enabled for your setup.

### Can I offer packages like 5 or 10 sessions?

Yes. Touch supports package/course options when they are configured for your
services.

### Which languages are supported?

The client Mini App supports Russian and Ukrainian. Ukrainian is shown for
Telegram users whose language starts with `uk`; otherwise Russian is used by
default.

### Can regular clients see admin controls?

No. Admin controls are shown only to allowed Telegram admin IDs.

### What happens if Railway or Telegram has an outage?

The app depends on Telegram and the hosting provider. Support can include basic
monitoring and troubleshooting, but third-party outages are outside the app's
control.

### Can this be customized for another local service business?

Yes. The same system can work for wellness, beauty, coaching, repair, lessons,
or other appointment-based local services.

### Do you guarantee more clients?

No. Touch improves booking convenience and reduces admin work, but marketing
results depend on the business, offer, traffic, and client communication.
