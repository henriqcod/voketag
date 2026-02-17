package middleware

import (
	"net/http"

	"github.com/voketag/scan-service/pkg/utils"
)

func ValidateUUID(paramName string) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tagID := r.PathValue(paramName)
			if tagID == "" {
				tagID = r.URL.Query().Get(paramName)
			}
			if tagID == "" || !utils.IsValidUUID(tagID) {
				w.WriteHeader(http.StatusBadRequest)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
