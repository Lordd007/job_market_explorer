// web/src/lib/__tests__/api.test.ts
import { fetchJSON, apiUrl } from "../api";

declare global {
  // keep TS happy when we stub fetch
  // eslint-disable-next-line no-var
  var fetch: jest.Mock;
}

describe("apiUrl", () => {
  it("builds correct URL with query parameters", () => {
    const u = apiUrl("/api/skills/top", {
      city: "New York",
      limit: 10,
      days: 30,
    });

    // u is a URL object
    expect(String(u)).toMatch(
      /^http:\/\/127\.0\.0\.1:8000\/api\/skills\/top\?/
    );

    expect(u.searchParams.get("city")).toBe("New York");
    expect(u.searchParams.get("limit")).toBe("10");
    expect(u.searchParams.get("days")).toBe("30");
  });
});

describe("fetchJSON", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("calls fetch with the correct URL and returns JSON", async () => {
    const mockData = [{ skill: "Python", cnt: 120 }];

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await fetchJSON("/api/skills/top", {
      params: { city: "Boston", limit: 5 },
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);

    const calledUrl: string = global.fetch.mock.calls[0][0];
    expect(calledUrl).toContain("/api/skills/top");
    expect(calledUrl).toContain("city=Boston");
    expect(calledUrl).toContain("limit=5");

    expect(result).toEqual(mockData);
  });

  it("throws an error if fetch fails", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    await expect(
      fetchJSON("/api/skills/top", { params: { city: "Chicago" } })
    ).rejects.toThrow(/HTTP 500/); // matches "HTTP 500: Internal Server Error"
  });
});
