-- 0 duplicates by binary desc_hash
SELECT COUNT(*) FROM (
  SELECT desc_hash FROM jobs WHERE desc_hash IS NOT NULL
  GROUP BY desc_hash HAVING COUNT(*) > 1
) x;

-- recent rows have desc_hash populated
SELECT COUNT(*) FROM jobs
WHERE created_at >= NOW() - INTERVAL '90 days' AND desc_hash IS NULL;

-- url_hash uniqueness solid
SELECT COUNT(*) FROM (
  SELECT url_hash FROM jobs WHERE url_hash IS NOT NULL
  GROUP BY url_hash HAVING COUNT(*) > 1
) x;