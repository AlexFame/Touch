import { memo } from "react";

export function Shell({ children }) {
  return (
    <main>
      <div className="app-swipe-layer">
        <div className="bg-orb one" />
        <div className="bg-orb two" />
        {children}
      </div>
    </main>
  );
}

export const StableImage = memo(function StableImage({
  alt = "",
  className,
  height,
  src,
  width,
}) {
  return (
    <img
      src={src}
      className={className}
      alt={alt}
      width={width}
      height={height}
      loading="eager"
      decoding="async"
      draggable="false"
    />
  );
});

export function TopBar({ title, onBack }) {
  return (
    <div className="topbar">
      <button onClick={onBack}>‹</button>
      <h2>{title}</h2>
      <span />
    </div>
  );
}

export function ServiceCard({ actionLabel, service, onClick, tr }) {
  const meta = service.package_sessions
    ? `${service.package_sessions} ${tr.sessions} · ${service.price_eur}€${
        service.package_original_price
          ? ` ${tr.insteadOf} ${service.package_original_price}€`
          : ""
      }`
    : `${service.duration_minutes} ${tr.min} · ${service.price_eur}€`;

  return (
    <button className="service-card" onClick={onClick}>
      <div>
        <h3>{service.option_title || service.title.split(" - ")[0]}</h3>
        <p>{meta}</p>
      </div>
      <span>{actionLabel || tr.select}</span>
    </button>
  );
}

export function Summary({ service, day, slot, duration, bonus, tr, lang, formatDay }) {
  if (!service) return null;
  const formatted = day ? formatDay(day.iso, lang) : null;
  const meta = service.package_sessions
    ? `${service.package_sessions} ${tr.sessions} · ${service.price_eur}€`
    : `${duration || service.duration_minutes} ${tr.min} · ${service.price_eur}€`;
  return (
    <div className="summary">
      <b>{service.title.split(" - ")[0]}</b>
      <span>{meta}</span>
      {formatted && (
        <span>
          {formatted.day} {formatted.month}
          {slot ? ` · ${slot}` : ""}
        </span>
      )}
      {bonus && <span className="green">+15 {tr.min} {tr.free}</span>}
    </div>
  );
}

export function EmptySlots({ imageSources, tr }) {
  return (
    <div className="empty">
      <StableImage
        src={imageSources.noSlots}
        className="cat-img-md"
        width={160}
        height={160}
      />
      <h3>{tr.noSlotsTitle}</h3>
      <p>{tr.noSlotsSubtitle}</p>
    </div>
  );
}

export function ErrorBox({ text }) {
  return <div className="error">{text}</div>;
}

export function CalendarGrid({ days, lang, selectedDay, onSelect, tr }) {
  if (!days || days.length === 0) return null;

  // Найти день недели первого дня (0=вс,1=пн,...6=сб) -> привести к пн=0
  const firstDate = new Date(days[0].iso + "T12:00:00");
  const lastDate = new Date(days[days.length - 1].iso + "T12:00:00");
  const firstWeekday = (firstDate.getDay() + 6) % 7; // пн=0, вт=1 ... вс=6
  const locale = lang === "uk" ? "uk-UA" : "ru-RU";
  const monthFormatter = new Intl.DateTimeFormat(locale, { month: "long" });
  const yearFormatter = new Intl.DateTimeFormat(locale, { year: "numeric" });
  const sameMonth =
    firstDate.getMonth() === lastDate.getMonth() &&
    firstDate.getFullYear() === lastDate.getFullYear();
  const monthTitle = sameMonth
    ? `${monthFormatter.format(firstDate)} ${yearFormatter.format(firstDate)}`
    : `${monthFormatter.format(firstDate)} - ${monthFormatter.format(lastDate)} ${yearFormatter.format(lastDate)}`;

  // Пустые ячейки в начале
  const empties = Array(firstWeekday).fill(null);

  return (
    <div className="cal-wrap">
      <div className="cal-month">{monthTitle}</div>
      <div className="cal-weekdays">
        {tr.weekdays.map((w) => (
          <div key={w} className="cal-wd">{w}</div>
        ))}
      </div>
      <div className="cal-grid">
        {empties.map((_, i) => (
          <div key={"e" + i} className="cal-empty" />
        ))}
        {days.map((d) => {
          const date = new Date(d.iso + "T12:00:00");
          const num = date.getDate();
          const isActive = selectedDay?.iso === d.iso;
          return (
            <button
              key={d.iso}
              className={"cal-day" + (isActive ? " active" : "")}
              onClick={() => onSelect(d)}
            >
              {num}
            </button>
          );
        })}
      </div>
    </div>
  );
}
