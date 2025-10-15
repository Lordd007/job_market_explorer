import { fetchJSON, apiUrl } from "../api";

describe("apiUrl", () => {
  it("builds correct URL with query parameters", () => {
    const result = apiUrl("/api/skills/top", {
      city: "New York",
      limit: 10,
      days: 30,
    });

    expect(result).toMatch(
      /^http:\/\/127\.0\.0\.1:8000\/api\/skills\/top\?(.+)/
    );
    expect(result).toContain("city=New%20York");
    expect(result).toContain("limit=10");
    expect(result).toContain("days=30");
  });
});

describe("fetchJSON", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("calls fetch with the correct URL and returns JSON", async () => {
    const mockData = [{ skill: "Python", cnt: 120 }];
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await fetchJSON("/api/skills/top", {
      city: "Boston",
      limit: 5,
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    const calledUrl = (fetch as jest.Mock).mock.calls[0][0];
    expect(calledUrl).toContain("/api/skills/top");
    expect(calledUrl).toContain("city=Boston");
    expect(calledUrl).toContain("limit=5");
    expect(result).toEqual(mockData);
  });

  it("throws an error if fetch fails", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    await expect(
      fetchJSON("/api/skills/top", { city: "Chicago" })
    ).rejects.toThrow("HTTP 500");
  });
});
