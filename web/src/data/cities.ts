export const CITIES_US = [
  "San Francisco", "New York", "Seattle", "Austin", "Boston",
  "Los Angeles", "Chicago", "Denver", "Atlanta", "Remote"
];

export const CITIES_UK = [
  "London", "Manchester", "Birmingham", "Leeds", "Edinburgh",
  "Glasgow", "Bristol", "Cambridge", "Oxford", "Remote"
];

export const ALL_CITIES = [
  ...CITIES_US.map(c => ({ country: "US", name: c })),
  ...CITIES_UK.map(c => ({ country: "UK", name: c })),
];
