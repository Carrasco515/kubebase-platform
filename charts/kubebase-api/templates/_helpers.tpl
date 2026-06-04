{{/*
Chart name (overridable via nameOverride).
*/}}
{{- define "kubebase-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Full release name (overridable via fullnameOverride).
*/}}
{{- define "kubebase-api.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Chart name and version, for the helm.sh/chart label.
*/}}
{{- define "kubebase-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels applied to all resources.
*/}}
{{- define "kubebase-api.labels" -}}
helm.sh/chart: {{ include "kubebase-api.chart" . }}
{{ include "kubebase-api.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: kubebase-platform
{{- end -}}

{{/*
Selector labels — stable across upgrades (do NOT add version here).
*/}}
{{- define "kubebase-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kubebase-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end -}}

{{/*
Name of the ServiceAccount to use.
*/}}
{{- define "kubebase-api.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "kubebase-api.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
