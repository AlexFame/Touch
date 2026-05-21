# Touch Client Intake Form

Use this form before setting up a new Touch client. Fill in every section before
creating Railway services, configuring Telegram, or changing app content.

## Business Details

- Business/studio name:
- Legal/business owner name:
- Public contact person:
- Studio address:
- City/country:
- Timezone:
- Public phone:
- Public Telegram username:
- Public Instagram/website:
- Business description:
- Any legal disclaimers clients must see:

## Services, Prices, And Durations

For each service, collect:

- Service name in Russian:
- Service name in Ukrainian:
- Short Mini App description in Russian:
- Short Mini App description in Ukrainian:
- Full description if needed:
- Duration in minutes:
- Price in EUR:
- Is this service available for online booking?
- Is first-visit bonus allowed for this service?
- Special notes, age limits, contraindications, or consent requirements:

Service table:

| Service | Duration | Price | RU title | UK title | Online booking | Notes |
| --- | ---: | ---: | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## Package And Course Options

For each service package/course:

- Related service:
- Number of sessions:
- Package price:
- Original full price:
- Discount shown to client:
- Package validity period:
- Should one booking create a package balance?
- Should completed visits deduct from package balance?
- Any package-specific cancellation or no-show rules:

Package table:

| Service | Sessions | Package price | Original price | Validity | Notes |
| --- | ---: | ---: | ---: | --- | --- |
|  |  |  |  |  |  |

## Working Hours And Booking Rules

- Business timezone:
- Working days:
- Start hour:
- End hour:
- Slot step in minutes:
- Buffer time after each booking:
- How many days ahead clients can book:
- Minimum notice before booking:
- Maximum bookings per client per day, if any:
- First-visit bonus duration:
- Which services should not receive first-visit bonus:
- Should admin be able to override availability?
- Holidays or blocked dates:
- Recurring breaks/lunch windows:

## Languages

- Client Mini App languages:
  - Russian:
  - Ukrainian:
- Default language:
- Telegram language behavior:
- Admin bot language:
- Google Calendar language:
- Any extra client-facing languages planned later:

## Telegram Bot And Admin Info

- BotFather bot username:
- Bot token:
- Bot display name:
- Bot description:
- Bot short description:
- Bot profile image:
- Mini App/Web App URL in BotFather:
- Admin Telegram IDs:
- Admin Telegram usernames:
- Which admins can manage bookings:
- Which admins only receive notifications:
- Should regular `/start` show only the Mini App open button?
- Any custom welcome message:

## Google Calendar And Review Info

- Google Calendar enabled:
- Google Calendar ID:
- Google account owner:
- Service account email:
- Has service account been shared into the calendar?
- Service account JSON collected:
- Calendar event title format:
- Calendar event description requirements:
- Buffer display in calendar description:
- Google review URL:
- When to send review request:
- Follow-up message after review request:

## Mini App Branding And Style

- Mini App title:
- Studio display name:
- Brand colors, if different from default:
- Logo or avatar source:
- Cat/mascot assets to replace:
- Confirmation image:
- Cancellation/reschedule images:
- Desired tone of voice:
- Address display text:
- Any text inside images that must not be translated:
- Any visual elements that must stay exactly as-is:

## Cancellation And Reschedule Rules

- Can clients cancel themselves?
- Can clients reschedule themselves?
- Latest allowed cancellation time:
- Latest allowed reschedule time:
- Should cancelled slots become available immediately?
- Should client receive cancellation notification?
- Should admin receive cancellation notification?
- Should Google Calendar event be deleted or updated?
- No-show policy:
- No-show count tracking needed:
- Reschedule keeps same booking record or creates a new one:
- Any fee or package deduction on cancellation/no-show:

## Client Follow-Up Preferences

- 24-hour reminder enabled:
- Reminder channel:
- Post-visit follow-up enabled:
- Follow-up delay:
- Google review request enabled:
- 7-10 day rebooking follow-up enabled:
- Follow-up language:
- Follow-up text style:
- Should package clients get different follow-ups?
- Should inactive clients receive comeback messages?
- Any messages the client must approve before launch:

## Deployment And Access

- Railway project owner:
- GitHub repository:
- Production branch:
- Backend API Railway URL:
- Mini App Railway URL:
- PostgreSQL service name:
- Backend service name:
- Bot Worker service name:
- Mini App service name:
- Who has Railway access:
- Who has GitHub access:
- Who has BotFather access:
- Who has Google Cloud/Calendar access:

## Launch Checklist Inputs

- All services and prices approved:
- All package options approved:
- All admin IDs confirmed:
- Bot token added to Railway:
- Google Calendar access confirmed:
- Google review URL confirmed:
- Mini App URL added to BotFather:
- `WEBAPP_URL` set on Backend API and Bot Worker:
- `VITE_API_URL` set on Mini App:
- Test booking completed:
- Test cancellation/reschedule completed:
- Admin controls verified:
- Regular client view verified:
