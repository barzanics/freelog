// Helper math functions
function dtr(d) { return (d * Math.PI) / 180; }
function rtd(r) { return (r * 180) / Math.PI; }
function fixHour(a) { return a - 24 * Math.floor(a / 24); }

// Julian date conversion (Gregorian to Julian Day)
function julian(year, month, day) {
  if (month <= 2) {
    year -= 1;
    month += 12;
  }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) +
         Math.floor(30.6001 * (month + 1)) +
         day + B - 1524.5;
}

// Sun position calculation: declination & equation of time
function sunPosition(jd) {
  const D = jd - 2451545.0;
  const g = fixAngle(357.529 + 0.98560028 * D);
  const q = fixAngle(280.459 + 0.98564736 * D);
  const L = fixAngle(q + 1.915 * Math.sin(dtr(g)) + 0.020 * Math.sin(dtr(2 * g)));

  const e = 23.439 - 0.00000036 * D;

  const RA = rtd(Math.atan2(Math.cos(dtr(e)) * Math.sin(dtr(L)), Math.cos(dtr(L)))) / 15;
  const eqt = q / 15 - fixHour(RA);
  const decl = Math.asin(Math.sin(dtr(e)) * Math.sin(dtr(L)));

  return { declination: decl, equation: eqt };
}

function fixAngle(a) {
  return a - 360 * Math.floor(a / 360);
}

// Mid-day (Dhuhr) time
function midDay(jDate, timeZone, longitude, approxTime) {
  const eqt = sunPosition(jDate + approxTime).equation;
  return fixHour(12 - eqt + timeZone - longitude / 15);
}

// Sun angle time (for Fajr, Sunrise, Sunset, Isha, Maghrib)
function sunAngleTime(jDate, timeZone, longitude, latitude, angle, ccw = true, approxTime = 0) {
  const decl = sunPosition(jDate + approxTime).declination;
  const noon = dtr(midDay(jDate, timeZone, longitude, approxTime));
  const lat = dtr(latitude);
  const a = dtr(angle);

  const t = Math.acos(
    (-Math.sin(a) - Math.sin(decl) * Math.sin(lat)) /
    (Math.cos(decl) * Math.cos(lat))
  ) / (Math.PI / 12); // convert rad to hours

  return fixHour(midDay(jDate, timeZone, longitude, approxTime) + (ccw ? -t : t));
}

// Convert fractional time to HH:mm string
function floatToTime24(time) {
  time = fixHour(time + 0.5 / 60); // add 0.5 minutes to round
  const hours = Math.floor(time);
  const minutes = Math.floor((time - hours) * 60);
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}
const SETTINGS = {
    fajrAngle: 17.7,
    ishaAngle: 14,
    maghribOffsetMinutes: 19, // Iran-wide average
};
  
// Main calculation function
function calculatePrayerTimes(date, latitude, longitude, timeZone = 3.5, dst = false) {
    if (dst) timeZone += 1;
  
    const { fajrAngle, ishaAngle, maghribOffsetMinutes } = SETTINGS;
  
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
  
    const jDate = julian(year, month, day) - longitude / (15 * 24);
  
    let times = {
      fajr: 5 / 24,
      sunrise: 6 / 24,
      dhuhr: 12 / 24,
      asr: 13 / 24,
      sunset: 18 / 24,
      maghrib: 18 / 24,
      isha: 18 / 24,
    };
  
    times.fajr = sunAngleTime(jDate, timeZone, longitude, latitude, fajrAngle, true, times.fajr);
    times.sunrise = sunAngleTime(jDate, timeZone, longitude, latitude, 0.833, true, times.sunrise);
    times.dhuhr = midDay(jDate, timeZone, longitude, times.dhuhr);
    times.asr = asrTime(jDate, timeZone, longitude, latitude, 1, times.asr);
    times.sunset = sunAngleTime(jDate, timeZone, longitude, latitude, 0.833, false, times.sunset);
    times.maghrib = fixHour(times.sunset + maghribOffsetMinutes / 60);
    times.isha = sunAngleTime(jDate, timeZone, longitude, latitude, ishaAngle, false, times.isha);
  
    // Midnight = middle of the night from maghrib to next day's fajr
    const fajrTomorrow = sunAngleTime(jDate + 1, timeZone, longitude, latitude, fajrAngle, true);
    const nightLength = timeDiff(times.sunset, fajrTomorrow);
    times.midnight = fixHour(times.sunset + nightLength / 2);
  
    return {
      imsak: floatToTime24(times.fajr - 5 / 60),
      fajr: floatToTime24(times.fajr),
      sunrise: floatToTime24(times.sunrise),
      dhuhr: floatToTime24(times.dhuhr),
      asr: floatToTime24(times.asr),
      sunset: floatToTime24(times.sunset),
      maghrib: floatToTime24(times.maghrib),
      isha: floatToTime24(times.isha),
      midnight: floatToTime24(times.midnight),
    };
}
  
  

// Time difference fix
function timeDiff(time1, time2) {
  return fixHour(time2 - time1);
}

// Calculate Asr time (shadow factor = 1 for standard)
function asrTime(jDate, timeZone, longitude, latitude, factor = 1, approxTime = 13 / 24) {
  const decl = sunPosition(jDate + approxTime).declination;
  const angle = -Math.atan(1 / (factor + Math.tan(Math.abs(dtr(latitude - rtd(decl))))));
  return sunAngleTime(jDate, timeZone, longitude, latitude, rtd(angle), false, approxTime);
}
