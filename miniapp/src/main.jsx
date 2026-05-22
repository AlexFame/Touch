import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookingFlow,
  CancelDoneScreen,
  DoneScreen,
  HomeScreen,
  MyBookingsScreen,
  PackageChoiceScreen,
  ServiceDetailsScreen,
  ServicesScreen,
} from "./screens";
import { UI_TEXT, apiLang, getInitialLang } from "./i18n";
import { ErrorBox, Shell } from "./ui";
import "./styles.css";

const API_BASE =
  import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? "";
const tg = window.Telegram?.WebApp;
const initData = tg?.initData || "";

const IMAGE_SOURCES = {
  hello: "/Привет 2.png",
  myBookings: "/Мои Записи 2.png",
  noBookings: "/no-bookings-cat.png",
  services: "/к Услугам.png",
  date: "/Дата.png",
  noSlots: "/Время на релакс.png",
  cancelled: "/cat-cancelled.png",
  rescheduled: "/cat-rescheduled.png",
  waitAgain: "/Жду вас снова.png",
  thanks: "/cat-thanks.png",
  booked: "/Запись подтверждена .png",
};

const PACKAGE_PRICES = {
  classic_back: {
    5: { price: 90, original: 100 },
    10: { price: 175, original: 200 },
  },
  relax: {
    5: { price: 90, original: 100 },
    10: { price: 175, original: 200 },
  },
  anti_cellulite: {
    5: { price: 135, original: 150 },
    10: { price: 260, original: 300 },
  },
  sport: {
    5: { price: 135, original: 150 },
    10: { price: 260, original: 300 },
  },
  child_wellness: {
    5: { price: 60, original: 75 },
    10: { price: 130, original: 150 },
  },
  general: {
    5: { price: 180, original: 200 },
    10: { price: 350, original: 400 },
  },
};

const STARTUP_IMAGE_SOURCES = [IMAGE_SOURCES.hello];
const DEFERRED_IMAGE_SOURCES = Object.values(IMAGE_SOURCES).filter(
  (src) => !STARTUP_IMAGE_SOURCES.includes(src),
);

const preloadedImages = new Map();

function preloadImage(src) {
  if (preloadedImages.has(src) || typeof window === "undefined") {
    return preloadedImages.get(src);
  }
  const image = new Image();
  image.decoding = "async";
  image.src = src;
  const decoded = image.decode?.().catch(() => undefined);
  const promise = decoded || Promise.resolve();
  preloadedImages.set(src, promise);
  return promise;
}

STARTUP_IMAGE_SOURCES.forEach(preloadImage);

function preloadDeferredImages() {
  if (typeof window === "undefined") return undefined;
  const preload = () => DEFERRED_IMAGE_SOURCES.forEach(preloadImage);

  if ("requestIdleCallback" in window) {
    const id = window.requestIdleCallback(preload);
    return () => window.cancelIdleCallback?.(id);
  }

  const id = window.setTimeout(preload, 300);
  return () => window.clearTimeout(id);
}

const SESSION_STATE_KEY = "massageMiniAppState:v1";
const VALID_STEPS = new Set([
  "home",
  "servicesInfo",
  "packageChoice",
  "service",
  "day",
  "time",
  "details",
  "done",
  "doneReschedule",
  "myBooking",
  "cancelDone",
]);

function readSavedState() {
  if (typeof window === "undefined") return {};
  try {
    const raw =
      window.sessionStorage.getItem(SESSION_STATE_KEY) ||
      window.localStorage.getItem(SESSION_STATE_KEY);
    if (!raw) return {};
    const data = JSON.parse(raw);
    if (!VALID_STEPS.has(data.step)) return {};
    if (!isRestorableState(data)) return {};
    return { ...data, restored: true };
  } catch {
    return {};
  }
}

function isRestorableState(data) {
  const needsService = data.step === "day" || data.step === "time" || data.step === "details";
  const needsDay = data.step === "time" || data.step === "details";

  if (data.step === "packageChoice" && !data.selectedInfoService) return false;
  if (needsService && !data.selectedService) return false;
  if (needsDay && !data.selectedDay) return false;
  if (data.step === "details" && !data.selectedSlot) return false;
  if ((data.step === "done" || data.step === "doneReschedule") && !data.booking) {
    return false;
  }
  if (data.step === "cancelDone" && !data.cancelledBooking) return false;
  if (data.step === "servicesInfo" && data.selectedInfoService && !data.selectedInfoService.id) {
    return false;
  }
  return true;
}

function saveState(data) {
  if (typeof window === "undefined") return;
  try {
    const raw = JSON.stringify(data);
    window.sessionStorage.setItem(SESSION_STATE_KEY, raw);
    window.localStorage.setItem(SESSION_STATE_KEY, raw);
  } catch {
    // Storage can be unavailable in some embedded WebViews.
  }
}

// Разворачиваем Mini App до максимальной высоты (без выхода из окна Telegram)
if (tg) {
  tg.expand();
}

function isTextInput(element) {
  return (
    element instanceof HTMLInputElement ||
    element instanceof HTMLTextAreaElement
  );
}

function blurActiveInput() {
  const active = document.activeElement;
  if (isTextInput(active)) active.blur();
}

function api(path, options = {}) {
  const fallbackError = UI_TEXT[getInitialLang(tg)].requestFailed;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (initData) headers["X-Telegram-Init-Data"] = initData;
  return fetch(`${API_BASE}${path}`, { ...options, headers }).then(
    async (r) => {
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        throw new Error(data.detail || fallbackError);
      }
      return r.json();
    },
  );
}

function formatDay(iso, lang = "ru") {
  const date = new Date(`${iso}T12:00:00`);
  const locale = lang === "uk" ? "uk-UA" : "ru-RU";
  return {
    day: new Intl.DateTimeFormat(locale, { day: "2-digit" }).format(date),
    month: new Intl.DateTimeFormat(locale, { month: "short" })
      .format(date)
      .replace(".", ""),
    weekday: new Intl.DateTimeFormat(locale, { weekday: "short" })
      .format(date)
      .replace(".", ""),
  };
}

function errorText(error, tr) {
  const message = error?.message || "";
  return tr.apiErrors?.[message] || message || tr.requestFailed;
}

const LINK_PATTERN = /(https?:\/\/|www\.|t\.me\/|telegram\.me\/|\S+\.\S{2,})/i;
const NAME_PATTERN = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’ -]+$/;
const USERNAME_PATTERN = /^@[A-Za-z0-9_]{5,32}$/;
const PHONE_PATTERN = /^\+?[0-9][0-9 ()-]{5,20}[0-9]$/;

function normalizeName(value) {
  return value
    .trim()
    .replace(/[^\p{L}'’ -]+/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

function isValidName(value) {
  const clean = normalizeName(value);
  return (
    clean.length >= 2 &&
    clean.length <= 60 &&
    !LINK_PATTERN.test(value) &&
    !/\p{N}/u.test(value) &&
    NAME_PATTERN.test(clean) &&
    [...clean].some((char) => /\p{L}/u.test(char))
  );
}

function normalizeContact(value) {
  const clean = value.trim();
  if (!clean) return "";
  if (clean.startsWith("@")) return clean;
  if (/\d/.test(clean)) return clean;
  return `@${clean}`;
}

function isValidContact(value) {
  const clean = normalizeContact(value);
  if (!clean) return true;
  if (LINK_PATTERN.test(clean)) return false;
  if (clean.startsWith("@")) return USERNAME_PATTERN.test(clean);
  const digits = clean.replace(/\D/g, "");
  return digits.length >= 7 && digits.length <= 15 && PHONE_PATTERN.test(clean);
}

function serviceBaseTitle(service) {
  return service.title.split(" - ")[0];
}


function App() {
  const [lang] = useState(() => getInitialLang(tg));
  const tr = UI_TEXT[lang];
  const backendLang = apiLang(lang);
  const [initialState] = useState(readSavedState);
  const [step, setStep] = useState(initialState.step || "home");
  const [bookingSource, setBookingSource] = useState(
    initialState.bookingSource || "service",
  );
  const [me, setMe] = useState(null);
  const [services, setServices] = useState([]);
  const [days, setDays] = useState([]);
  const [slots, setSlots] = useState(initialState.slots || []);
  const [selectedService, setSelectedService] = useState(
    initialState.selectedService || null,
  );
  const [selectedInfoService, setSelectedInfoService] = useState(
    initialState.selectedInfoService || null,
  );
  const [selectedDay, setSelectedDay] = useState(initialState.selectedDay || null);
  const [selectedSlot, setSelectedSlot] = useState(
    initialState.selectedSlot || null,
  );
  const [slotMeta, setSlotMeta] = useState(initialState.slotMeta || null);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [name, setName] = useState(initialState.name || "");
  const [contact, setContact] = useState(initialState.contact || "");
  const [booking, setBooking] = useState(initialState.booking || null);
  const [activeBookings, setActiveBookings] = useState(
    initialState.activeBookings || [],
  );
  const [cancelledBooking, setCancelledBooking] = useState(
    initialState.cancelledBooking || null,
  );
  const [rescheduleBookingId, setRescheduleBookingId] = useState(
    initialState.rescheduleBookingId || null,
  );
  const [loading, setLoading] = useState(!initialState.restored);
  const [error, setError] = useState("");

  useEffect(() => {
    const currentState = {
      step,
      bookingSource,
      selectedService,
      selectedInfoService,
      selectedDay,
      selectedSlot,
      slotMeta,
      slots,
      name,
      contact,
      booking,
      activeBookings,
      cancelledBooking,
      rescheduleBookingId,
    };
    saveState(currentState);

    const saveCurrentState = () => saveState(currentState);
    window.addEventListener("pagehide", saveCurrentState);
    document.addEventListener("visibilitychange", saveCurrentState);
    return () => {
      window.removeEventListener("pagehide", saveCurrentState);
      document.removeEventListener("visibilitychange", saveCurrentState);
    };
  }, [
    step,
    bookingSource,
    selectedService,
    selectedInfoService,
    selectedDay,
    selectedSlot,
    slotMeta,
    slots,
    name,
    contact,
    booking,
    activeBookings,
    cancelledBooking,
    rescheduleBookingId,
  ]);

  useEffect(() => {
    tg?.ready?.();
    const cancelDeferredPreload = preloadDeferredImages();
    Promise.all([
      api("/api/me"),
      api(`/api/services?lang=${backendLang}`),
      api("/api/days"),
    ])
      .then(([meData, servicesData, daysData]) => {
        setMe(meData);
        setName((current) =>
          current || meData.name || tg?.initDataUnsafe?.user?.first_name || "",
        );
        setContact((current) => current || meData.contact || meData.phone || "");
        setServices(servicesData);
        setDays(daysData);
        setLoading(false);
      })
      .catch((e) => {
        setError(errorText(e, tr));
        setLoading(false);
      });
    return cancelDeferredPreload;
  }, [backendLang, tr]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const root = document.documentElement;
    let baseHeight = window.innerHeight;

    const updateViewport = () => {
      const viewport = window.visualViewport;
      const visibleHeight = viewport?.height || window.innerHeight;
      const offsetTop = viewport?.offsetTop || 0;
      const keyboardInset = Math.max(
        0,
        baseHeight - visibleHeight - offsetTop,
      );

      if (keyboardInset < 80) {
        baseHeight = Math.max(baseHeight, window.innerHeight, visibleHeight);
      }

      const keyboardOpen = keyboardInset >= 80;
      const appHeight = baseHeight;

      root.style.setProperty("--app-height", `${appHeight}px`);
      root.style.setProperty("--keyboard-inset", `${keyboardInset}px`);
      root.classList.toggle("keyboard-open", keyboardOpen);
    };

    const onPointerDown = (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (target.closest("input, textarea, select")) return;
      blurActiveInput();
    };

    const onFocusIn = (event) => {
      if (!isTextInput(event.target)) return;
      window.setTimeout(() => {
        event.target
          .closest(".field")
          ?.scrollIntoView({ block: "center", behavior: "smooth" });
      }, 80);
    };

    updateViewport();
    window.visualViewport?.addEventListener("resize", updateViewport);
    window.visualViewport?.addEventListener("scroll", updateViewport);
    window.addEventListener("resize", updateViewport);
    document.addEventListener("pointerdown", onPointerDown, true);
    document.addEventListener("focusin", onFocusIn);

    return () => {
      window.visualViewport?.removeEventListener("resize", updateViewport);
      window.visualViewport?.removeEventListener("scroll", updateViewport);
      window.removeEventListener("resize", updateViewport);
      document.removeEventListener("pointerdown", onPointerDown, true);
      document.removeEventListener("focusin", onFocusIn);
      root.classList.remove("keyboard-open");
      root.style.removeProperty("--app-height");
      root.style.removeProperty("--keyboard-inset");
    };
  }, []);

  useEffect(() => {
    if (!selectedService || !selectedDay) return;
    let cancelled = false;
    setSlotsLoading(true);
    setSlots([]);
    setSlotMeta(null);
    api(
      `/api/slots?service_id=${selectedService.id}&day_iso=${selectedDay.iso}`,
    )
      .then((data) => {
        if (cancelled) return;
        setSlots(data.slots);
        setSlotMeta(data);
      })
      .catch((e) => {
        if (!cancelled) setError(errorText(e, tr));
      })
      .finally(() => {
        if (!cancelled) setSlotsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedService, selectedDay, tr]);

  const totalDuration =
    slotMeta?.duration_minutes || selectedService?.duration_minutes || 0;
  const bonus = Boolean(slotMeta?.first_visit_bonus_applied);
  const canSubmitDetails = isValidName(name) && isValidContact(contact);
  const packageOptions = selectedInfoService
    ? createPackageOptions(selectedInfoService, tr)
    : [];

  function createPackageOptions(service, text) {
    const prices = PACKAGE_PRICES[service.id] || {};
    const baseTitle = serviceBaseTitle(service);
    return [
      {
        ...service,
        title: `${baseTitle} - ${text.singleSession} - ${service.price_eur}€`,
        option_title: text.singleSession,
        package_sessions: null,
        package_original_price: null,
        is_package: false,
      },
      ...[5, 10]
        .filter((sessions) => prices[sessions])
        .map((sessions) => ({
          ...service,
          id: `${service.id}_package_${sessions}`,
          title: `${baseTitle} - ${sessions} ${text.sessions} - ${prices[sessions].price}€`,
          option_title: sessions === 5 ? text.course5 : text.course10,
          price_eur: prices[sessions].price,
          package_sessions: sessions,
          package_original_price: prices[sessions].original,
          is_package: true,
        })),
    ];
  }

  function startBooking(serviceToBook, source = "servicesInfo") {
    setSelectedService(serviceToBook);
    setSelectedInfoService(null);
    setSelectedDay(null);
    setSelectedSlot(null);
    setSlotMeta(null);
    setSlots([]);
    setBookingSource(source);
    setStep("day");
  }

  async function submitBooking() {
    blurActiveInput();
    setError("");
    const cleanName = normalizeName(name);
    const cleanContact = normalizeContact(contact);
    if (!isValidName(cleanName)) {
      setError(tr.invalidName);
      return;
    }
    if (!isValidContact(cleanContact)) {
      setError(tr.invalidContact);
      return;
    }
    try {
      const payload = {
        service_id: selectedService.id,
        day_iso: selectedDay.iso,
        slot: selectedSlot,
        name: cleanName,
        contact: cleanContact,
        lang: backendLang,
      };
      if (rescheduleBookingId) {
        const result = await api(
          `/api/bookings/${rescheduleBookingId}/reschedule`,
          {
            method: "POST",
            body: JSON.stringify(payload),
          },
        );
        setBooking(result);
        setStep("doneReschedule");
      } else {
        const result = await api("/api/bookings", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setBooking(result);
        setStep("done");
      }
    } catch (e) {
      setError(errorText(e, tr));
    }
  }

  async function loadMyBookings() {
    setError("");
    preloadImage(IMAGE_SOURCES.myBookings);
    preloadImage(IMAGE_SOURCES.noBookings);
    try {
      const result = await api(`/api/active-bookings?lang=${backendLang}`);
      setActiveBookings(result || []);
      setStep("myBooking");
    } catch (e) {
      setError(errorText(e, tr));
    }
  }

  async function cancelBooking(bookingToCancel) {
    if (!confirm(tr.cancelConfirm)) return;

    setError("");

    try {
      await api(`/api/bookings/${bookingToCancel.id}/cancel`, {
        method: "POST",
      });
      setCancelledBooking(bookingToCancel);
      setStep("cancelDone");
    } catch (e) {
      setError(errorText(e, tr) || tr.cancelFailed);
    }
  }

  function startReschedule(bookingToReschedule) {
    setRescheduleBookingId(bookingToReschedule.id);
    setBookingSource("myBooking");
    setSelectedInfoService(null);
    setSelectedDay(null);
    setSelectedSlot(null);
    setSlotMeta(null);
    setSlots([]);
    setBooking(null);
    setError("");
    setSelectedService({
      id: bookingToReschedule.service_id,
      title: bookingToReschedule.title,
      duration_minutes: bookingToReschedule.duration_minutes,
      price_eur: bookingToReschedule.price_eur,
      is_package: bookingToReschedule.is_package,
      package_sessions: bookingToReschedule.package_sessions,
    });
    setStep("day");
  }

  function goHome() {
    setRescheduleBookingId(null);
    setSelectedService(null);
    setSelectedInfoService(null);
    setSelectedDay(null);
    setSelectedSlot(null);
    setSlotMeta(null);
    setSlots([]);
    setSlotsLoading(false);
    setBooking(null);
    setCancelledBooking(null);
    setActiveBookings([]);
    setBookingSource("service");
    setError("");
    setStep("home");
  }

  function goBack() {
    if (step === "servicesInfo" && selectedInfoService) {
      setSelectedInfoService(null);
      return;
    }

    const backMap = {
      servicesInfo: "home",
      packageChoice: "servicesInfo",
      service: "home",
      day: bookingSource,
      time: "day",
      details: "time",
      myBooking: "home",
      done: "home",
      doneReschedule: "myBooking",
      cancelDone: "home",
    };
    const prev = backMap[step];
    if (prev) setStep(prev);
  }

  useEffect(() => {
    if (step === "home") return;
    let startX = 0;
    let startY = 0;
    let dragging = false;
    let locked = false;
    let cancelled = false;
    const getEl = () => document.querySelector("main > section");

    const onTouchStart = (e) => {
      if (e.touches[0].clientX > 40) return;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      dragging = true;
      locked = false;
      cancelled = false;
    };

    const onTouchMove = (e) => {
      if (!dragging || cancelled) return;
      const dx = e.touches[0].clientX - startX;
      const dy = Math.abs(e.touches[0].clientY - startY);
      if (!locked) {
        if (dx < 8 && dy < 8) return;
        if (dy > dx) { cancelled = true; return; }
        locked = true;
      }
      if (dy > 60 || dx < 0) { cancelled = true; return; }
      e.preventDefault();
      const el = getEl();
      if (el) {
        el.style.transform = `translate3d(${dx}px, 0, 0)`;
        el.style.transition = "none";
        el.style.boxShadow = `-${dx * 0.15}px 0 30px rgba(0,0,0,0.4)`;
      }
    };

    const onTouchEnd = (e) => {
      if (!dragging) return;
      dragging = false;
      const el = getEl();
      if (cancelled || !el) {
        if (el) { el.style.transform = ""; el.style.transition = ""; el.style.boxShadow = ""; }
        cancelled = false;
        return;
      }
      const dx = e.changedTouches[0].clientX - startX;
      if (dx > 90) {
        tg?.HapticFeedback?.impactOccurred("light");
        el.style.transition = "transform 0.22s ease-out";
        el.style.transform = `translate3d(${window.innerWidth}px, 0, 0)`;
        setTimeout(() => {
          goBack();
          el.style.transform = "";
          el.style.transition = "";
          el.style.boxShadow = "";
        }, 220);
      } else {
        el.style.transition = "transform 0.3s ease-out";
        el.style.transform = "";
        el.style.boxShadow = "";
        setTimeout(() => { el.style.transition = ""; }, 300);
      }
    };

    document.addEventListener("touchstart", onTouchStart, { passive: true });
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("touchend", onTouchEnd, { passive: true });
    return () => {
      document.removeEventListener("touchstart", onTouchStart);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("touchend", onTouchEnd);
    };
  }, [step, bookingSource, selectedInfoService]);

  if (loading) {
    return (
      <Shell>
        <div className="loader">{tr.loading}</div>
      </Shell>
    );
  }

  if (error && !me) {
    return (
      <Shell>
        <ErrorBox text={error} />
      </Shell>
    );
  }

  const sectionClassName = getSectionClassName(step);

  return (
    <Shell>
      <section className={sectionClassName}>
        <div className="screen-content">
          {step === "home" && (
            <HomeScreen
              error={error}
              imageSources={IMAGE_SOURCES}
              onBook={() => {
                setSelectedInfoService(null);
                setBookingSource("service");
                setStep("service");
              }}
              onMyBookings={loadMyBookings}
              onServices={() => {
                setSelectedInfoService(null);
                setStep("servicesInfo");
              }}
              tr={tr}
            />
          )}

          {step === "myBooking" && (
            <MyBookingsScreen
              activeBookings={activeBookings}
              formatDay={formatDay}
              imageSources={IMAGE_SOURCES}
              lang={lang}
              onBack={goHome}
              onBook={() => {
                setSelectedInfoService(null);
                setBookingSource("service");
                setStep("service");
              }}
              onCancel={cancelBooking}
              onReschedule={startReschedule}
              tr={tr}
            />
          )}

          {step === "cancelDone" && (
            <CancelDoneScreen
              cancelledBooking={cancelledBooking}
              formatDay={formatDay}
              imageSources={IMAGE_SOURCES}
              lang={lang}
              onHome={goHome}
              onMyBookings={async () => {
                setError("");
                preloadImage(IMAGE_SOURCES.myBookings);
                preloadImage(IMAGE_SOURCES.noBookings);
                try {
                  const updated = await api(`/api/active-bookings?lang=${backendLang}`);
                  setActiveBookings(updated || []);
                  setCancelledBooking(null);
                  setStep("myBooking");
                } catch (e) {
                  setError(errorText(e, tr) || tr.noBookingsLoadFailed);
                }
              }}
              tr={tr}
            />
          )}

          {step === "servicesInfo" && (
            selectedInfoService ? (
              <ServiceDetailsScreen
                imageSrc={IMAGE_SOURCES.services}
                onBack={() => setSelectedInfoService(null)}
                onBook={() => {
                  if (packageOptions.length > 1) {
                    setStep("packageChoice");
                    return;
                  }
                  startBooking(selectedInfoService, "servicesInfo");
                }}
                service={selectedInfoService}
                tr={tr}
              />
            ) : (
              <ServicesScreen
                actionLabel={tr.moreDetails}
                imageSrc={IMAGE_SOURCES.services}
                onBack={() => setStep("home")}
                onSelectService={setSelectedInfoService}
                services={services}
                title={tr.servicesAndPrices}
                tr={tr}
              />
            )
          )}

          {step === "packageChoice" && selectedInfoService && (
            <PackageChoiceScreen
              onBack={() => setStep("servicesInfo")}
              onSelect={(option) => startBooking(option, "servicesInfo")}
              options={packageOptions}
              service={selectedInfoService}
              tr={tr}
            />
          )}

          {step === "service" && (
            <ServicesScreen
              imageSrc={IMAGE_SOURCES.date}
              onBack={() => setStep("home")}
              onSelectService={(s) => {
                startBooking(s, "service");
              }}
              services={services}
              title={tr.chooseMassage}
              tr={tr}
            />
          )}

          {(step === "day" || step === "time" || step === "details") && (
            <BookingFlow
              bonus={bonus}
              contact={contact}
              canSubmit={canSubmitDetails}
              days={days}
              error={error}
              formatDay={formatDay}
              imageSources={IMAGE_SOURCES}
              lang={lang}
              name={name}
              onBackToBookingSource={() => setStep(bookingSource)}
              onChooseTime={() => setStep("time")}
              onContactChange={setContact}
              onNameChange={setName}
              onSelectDay={(day) => {
                setSelectedSlot(null);
                setSelectedDay(day);
              }}
              onSelectSlot={setSelectedSlot}
              onSubmit={submitBooking}
              onTimeBack={() => setStep("day")}
              rescheduleBookingId={rescheduleBookingId}
              selectedDay={selectedDay}
              selectedService={selectedService}
              selectedSlot={selectedSlot}
              setStep={setStep}
              slots={slots}
              slotsLoading={slotsLoading}
              step={step}
              totalDuration={totalDuration}
              tr={tr}
            />
          )}

          {step === "doneReschedule" && (
            <DoneScreen
              booking={booking}
              imageSrc={IMAGE_SOURCES.rescheduled}
              isReschedule
              onHome={goHome}
              tr={tr}
            />
          )}

          {step === "done" && (
            <DoneScreen
              booking={booking}
              imageSrc={IMAGE_SOURCES.booked}
              onHome={goHome}
              tr={tr}
            />
          )}
        </div>
      </section>
    </Shell>
  );
}

function getSectionClassName(step) {
  if (step === "home") return "hero";
  if (
    step === "day" ||
    step === "time" ||
    step === "details" ||
    step === "doneReschedule" ||
    step === "done" ||
    step === "cancelDone"
  ) {
    return "section-sticky";
  }
  return undefined;
}


createRoot(document.getElementById("root")).render(<App />);
