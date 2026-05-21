import {
  CalendarDays,
  Clock,
  PawPrint,
} from "lucide-react";
import {
  CalendarGrid,
  EmptySlots,
  ErrorBox,
  ServiceCard,
  StableImage,
  Summary,
  TopBar,
} from "./ui";

export function HomeScreen({
  error,
  imageSources,
  onBook,
  onMyBookings,
  onServices,
  tr,
}) {
  return (
    <>
      <div className="hero-card">
        <p className="eyebrow">
          <PawPrint size={16} /> {tr.massageAssistant}
        </p>
        <h1>{tr.homeTitle}</h1>
        <p className="muted">
          {tr.homeSubtitle}
        </p>
        <StableImage
          src={imageSources.hello}
          className="cat-img"
          width={220}
          height={240}
        />
        <div className="bonus">
          {tr.firstVisitBonus}
        </div>
      </div>
      <button className="primary" onClick={onBook}>
        {tr.book}
      </button>
      <button className="secondary" onClick={onServices}>
        {tr.servicesAndPrices}
      </button>
      <button
        className="secondary"
        onClick={onMyBookings}
        style={{ marginTop: "8px" }}
      >
        {tr.myBookings}
      </button>
      {error && <ErrorBox text={error} />}
    </>
  );
}

export function MyBookingsScreen({
  activeBookings,
  formatDay,
  imageSources,
  lang,
  onBack,
  onBook,
  onCancel,
  onReschedule,
  tr,
}) {
  return (
    <>
      <TopBar title={tr.myBookings} onBack={onBack} />
      {activeBookings.length === 0 ? (
        <>
          <StableImage
            src={imageSources.noBookings}
            className="services-hero-img"
            width={320}
            height={220}
          />
          <div
            className="empty"
            style={{ textAlign: "center", marginTop: "2rem" }}
          >
            <h3>{tr.noActiveBookings}</h3>
            <button
              className="primary"
              onClick={onBook}
              style={{ marginTop: "2.25rem" }}
            >
              {tr.book}
            </button>
          </div>
        </>
      ) : (
        <>
          <StableImage
            src={imageSources.myBookings}
            className="services-hero-img"
            width={320}
            height={220}
          />
          <div style={{ marginTop: "1rem" }}>
          {activeBookings.map((ab) => (
            <div
              key={ab.id}
              style={{
                marginBottom: "1.5rem",
                paddingBottom: "1.5rem",
                borderBottom: "1px solid var(--line)",
              }}
            >
              <div className="summary" style={{ marginBottom: "1rem" }}>
                <b>{ab.title.split(" - ")[0]}</b>
                <span>
                  {ab.duration_minutes} {tr.min} · {ab.price_eur}€
                </span>
                <span>
                  {formatDay(ab.starts_at.split("T")[0], lang).day}{" "}
                  {formatDay(ab.starts_at.split("T")[0], lang).month} ·{" "}
                  {ab.starts_at.split("T")[1].slice(0, 5)}
                </span>
                <span className="muted">
                  {tr.addressLabel}: {tr.studioAddress}
                </span>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  className="primary"
                  onClick={() => onReschedule(ab)}
                  style={{ flex: 1 }}
                >
                  {tr.reschedule}
                </button>
                <button
                  className="secondary"
                  onClick={() => onCancel(ab)}
                  style={{ flex: 1, color: "#ff4b4b" }}
                >
                  {tr.cancel}
                </button>
              </div>
            </div>
          ))}
          </div>
        </>
      )}
    </>
  );
}

export function CancelDoneScreen({
  cancelledBooking,
  formatDay,
  imageSources,
  lang,
  onHome,
  onMyBookings,
  tr,
}) {
  return (
    <>
      <div className="section-scroll done">
        <StableImage
          src={imageSources.cancelled}
          className="services-hero-img"
          width={320}
          height={220}
        />
        <h1>{tr.cancelledTitle}</h1>
        <p className="muted">{tr.cancelledSubtitle}</p>
        {cancelledBooking && (
          <div className="summary" style={{ marginTop: "1rem", marginBottom: "1rem" }}>
            <b>{(cancelledBooking.title || cancelledBooking.service_title || "").split(" - ")[0]}</b>
            {cancelledBooking.starts_at ? (
              <span>
                {formatDay(cancelledBooking.starts_at.split("T")[0], lang).day}{" "}
                {formatDay(cancelledBooking.starts_at.split("T")[0], lang).month} ·{" "}
                {cancelledBooking.starts_at.split("T")[1].slice(0, 5)}
              </span>
            ) : (
              <span>{cancelledBooking.date} {tr.at} {cancelledBooking.time}</span>
            )}
            <span>{cancelledBooking.duration_minutes} {tr.min} · {cancelledBooking.price_eur}€</span>
          </div>
        )}
      </div>
      <div className="section-footer">
        <button
          className="primary"
          style={{ marginTop: 0 }}
          onClick={onMyBookings}
        >
          {tr.myBookings}
        </button>
        <button className="secondary" onClick={onHome} style={{ marginTop: 0 }}>{tr.home}</button>
      </div>
    </>
  );
}

export function ServicesScreen({
  actionLabel,
  imageSrc,
  onBack,
  onSelectService,
  services,
  title,
  tr,
}) {
  return (
    <>
      <TopBar title={title} onBack={onBack} />
      <StableImage
        src={imageSrc}
        className="services-hero-img"
        width={320}
        height={220}
      />
      <div className="list">
        {services.map((s) => (
          <ServiceCard
            key={s.id}
            actionLabel={actionLabel}
            service={s}
            tr={tr}
            onClick={() => onSelectService(s)}
          />
        ))}
      </div>
    </>
  );
}

export function ServiceDetailsScreen({
  imageSrc,
  onBack,
  onBook,
  service,
  tr,
}) {
  return (
    <>
      <TopBar title={service.title.split(" - ")[0]} onBack={onBack} />
      <StableImage
        src={imageSrc}
        className="services-hero-img"
        width={320}
        height={220}
      />
      <div className="summary service-details">
        <b>{service.title.split(" - ")[0]}</b>
        <span>
          {service.duration_minutes} {tr.min} · {service.price_eur}€
        </span>
        <p>{tr.serviceDescriptions?.[service.id]}</p>
      </div>
      <button className="primary" onClick={onBook}>
        {tr.book}
      </button>
    </>
  );
}

export function PackageChoiceScreen({
  onBack,
  onSelect,
  options,
  service,
  tr,
}) {
  return (
    <>
      <TopBar title={tr.chooseBookingType} onBack={onBack} />
      <div className="summary service-details">
        <b>{service.title.split(" - ")[0]}</b>
        <span>
          {service.duration_minutes} {tr.min} · {service.price_eur}€
        </span>
      </div>
      <div className="list">
        {options.map((option) => (
          <ServiceCard
            key={option.id}
            actionLabel={tr.select}
            service={option}
            tr={tr}
            onClick={() => onSelect(option)}
          />
        ))}
      </div>
    </>
  );
}

export function BookingFlow({
  bonus,
  canSubmit,
  contact,
  days,
  error,
  formatDay,
  imageSources,
  lang,
  name,
  onBackToBookingSource,
  onChooseTime,
  onContactChange,
  onNameChange,
  onSelectDay,
  onSelectSlot,
  onSubmit,
  onTimeBack,
  rescheduleBookingId,
  selectedDay,
  selectedService,
  selectedSlot,
  setStep,
  slots,
  slotsLoading,
  step,
  totalDuration,
  tr,
}) {
  if (step === "day") {
    return (
      <>
        <div className="section-scroll">
          <TopBar title={tr.chooseDay} onBack={onBackToBookingSource} />
          <Summary service={selectedService} tr={tr} lang={lang} formatDay={formatDay} />
          <CalendarGrid
            days={days}
            selectedDay={selectedDay}
            tr={tr}
            onSelect={onSelectDay}
          />
        </div>
        <div className="section-footer">
          <button
            className="primary"
            disabled={!selectedDay || slotsLoading}
            onClick={onChooseTime}
            style={{ marginTop: 0 }}
          >
            {tr.chooseTime}
          </button>
        </div>
      </>
    );
  }

  if (step === "time") {
    return (
      <>
        <div className="section-scroll">
          <TopBar title={tr.freeTime} onBack={onTimeBack} />
          <Summary service={selectedService} day={selectedDay} tr={tr} lang={lang} formatDay={formatDay} />
          {bonus && (
            <div className="bonus time-bonus">
              {tr.firstVisitTimeBonus}
            </div>
          )}
          {slotsLoading ? null : slots.length === 0 ? (
            <EmptySlots imageSources={imageSources} tr={tr} />
          ) : (
            <div className="slots-grid">
              {slots.map((s) => (
                <button
                  className={`slot ${selectedSlot === s ? "active" : ""}`}
                  onClick={() => onSelectSlot(s)}
                  key={s}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="section-footer">
          <button
            className="primary"
            disabled={!selectedSlot}
            onClick={() => setStep("details")}
            style={{ marginTop: 0 }}
          >
            {tr.continue}
          </button>
        </div>
      </>
    );
  }

  const blurOnEnter = (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    event.currentTarget.blur();
  };

  return (
    <>
      <div className="section-scroll">
        <TopBar title={tr.details} onBack={() => setStep("time")} />
        <Summary
          service={selectedService}
          day={selectedDay}
          slot={selectedSlot}
          duration={totalDuration}
          bonus={bonus}
          tr={tr}
          lang={lang}
          formatDay={formatDay}
        />
        {rescheduleBookingId ? (
          <div
            className="summary"
            style={{
              marginBottom: "1rem",
            }}
          >
            <small className="muted">{tr.rescheduleNotice}</small>
            <b style={{ display: "block", marginTop: "4px" }}>
              → {tr.newTime}: {formatDay(selectedDay.iso, lang).day}{" "}
              {formatDay(selectedDay.iso, lang).month} · {selectedSlot}
            </b>
          </div>
        ) : null}
        <label className="field">
          {tr.name}
          <input
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            onKeyDown={blurOnEnter}
            maxLength={60}
            placeholder={tr.namePlaceholder}
          />
        </label>
        <label className="field">
          {tr.contactForReply}
          <input
            value={contact}
            onChange={(e) => onContactChange(e.target.value)}
            onKeyDown={blurOnEnter}
            maxLength={40}
            placeholder={tr.contactPlaceholder}
          />
          <small
            className="muted"
            style={{ display: "block", marginTop: "4px", fontSize: "0.85em" }}
          >
            {tr.contactHelp}
          </small>
        </label>
        {error && <ErrorBox text={error} />}
      </div>
      <div className="section-footer">
        <button className="primary" disabled={!canSubmit} onClick={onSubmit} style={{ marginTop: 0 }}>
          {rescheduleBookingId ? tr.confirmReschedule : tr.confirmBooking}
        </button>
      </div>
    </>
  );
}

export function DoneScreen({ booking, imageSrc, isReschedule, onHome, tr }) {
  return (
    <>
      <div className="section-scroll done">
        <StableImage
          src={imageSrc}
          className="services-hero-img"
          width={320}
          height={220}
        />
        <h1>{isReschedule ? tr.rescheduledTitle : tr.bookedTitle}</h1>
        {isReschedule ? (
          <p className="green" style={{ marginBottom: "1rem" }}>{tr.rescheduledSubtitle}</p>
        ) : null}
        {isReschedule ? <b>{booking.title}</b> : <p>{booking.title}</p>}
        <div className="done-card" style={isReschedule ? { marginTop: "1rem" } : undefined}>
          <CalendarDays size={18} /> {booking.date} {tr.at} {booking.time}
        </div>
        <div className="done-card">
          <Clock size={18} /> {booking.duration_minutes} {tr.min} · {booking.price_eur}€
        </div>
        <div className="done-card address-card">
          <b>{tr.addressLabel}</b>
          <span>{tr.studioAddress}</span>
        </div>
        <p className="muted">{tr.telegramConfirmation}</p>
      </div>
      <div className="section-footer">
        <button className="primary" onClick={onHome} style={{ marginTop: 0 }}>{tr.home}</button>
      </div>
    </>
  );
}
