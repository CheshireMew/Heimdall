import axios, {
    type AxiosInstance,
    type AxiosRequestConfig,
    type AxiosResponse,
    type InternalAxiosRequestConfig,
} from 'axios'
import {
    apiEndpoint,
    serializeEndpointQuery,
    type ApiRouteBody,
    type ApiRouteName,
    type ApiRouteQuery,
    type ApiRouteResponse,
    type RouteParams,
} from './routes'
import type { ApiErrorResponse } from './errors'

export class ApiRequestError extends Error {
    readonly detail: string
    readonly status: number | null
    readonly payload: ApiErrorResponse | null

    constructor(detail: string, options: { status?: number | null; payload?: ApiErrorResponse | null } = {}) {
        super(detail)
        this.name = 'ApiRequestError'
        this.detail = detail
        this.status = options.status ?? null
        this.payload = options.payload ?? null
    }
}

const isApiErrorResponse = (value: unknown): value is ApiErrorResponse => (
    typeof value === 'object'
    && value !== null
    && 'detail' in value
    && typeof (value as { detail?: unknown }).detail === 'string'
)

export const normalizeApiError = (error: unknown, fallback = 'Request failed'): ApiRequestError => {
    if (error instanceof ApiRequestError) return error
    if (axios.isAxiosError(error)) {
        const payload = isApiErrorResponse(error.response?.data) ? error.response.data : null
        const detail = payload?.detail || error.message || fallback
        return new ApiRequestError(detail, {
            status: error.response?.status ?? null,
            payload,
        })
    }
    if (error instanceof Error) return new ApiRequestError(error.message || fallback)
    return new ApiRequestError(fallback)
}

export const apiErrorMessage = (error: unknown, fallback: string): string => {
    const message = normalizeApiError(error, fallback).detail.trim()
    return message || fallback
}

const attachInterceptors = (client: AxiosInstance) => {
    client.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            return config
        },
        (error: unknown) => {
            return Promise.reject(error)
        }
    )

    client.interceptors.response.use(
        (response: AxiosResponse) => {
            return response
        },
        (error: unknown) => {
            if (!isRequestCanceled(error)) {
                console.error('API Request Failed:', error)
                return Promise.reject(normalizeApiError(error))
            }
            return Promise.reject(error)
        }
    )

    return client
}

const createClient = (timeout: number): AxiosInstance => attachInterceptors(
    axios.create({
        baseURL: '/api/v1',
        timeout,
        headers: {
            'Content-Type': 'application/json'
        }
    })
)

const apiClients = {
    default: createClient(15000),
    longTask: createClient(660000),
} as const

type ApiClientName = keyof typeof apiClients
type ApiOptions<TRoute extends ApiRouteName> = Omit<AxiosRequestConfig, 'params' | 'url' | 'method'> & {
    client?: ApiClientName
    path?: RouteParams
    query?: ApiRouteQuery<TRoute>
}

const querySerializerKey = ['params', 'Serializer'].join('')

const buildRequestConfig = <TRoute extends ApiRouteName>(name: TRoute, options: ApiOptions<TRoute> = {}): AxiosRequestConfig => {
    const { client: _client, path: _path, query, ...config } = options
    if (!query) return config
    return {
        ...config,
        params: query,
        // Axios is still the transport, but route-specific query rules live in generated endpoint contracts.
        [querySerializerKey]: () => serializeEndpointQuery(name, query),
    } as AxiosRequestConfig
}

const resolveClient = <TRoute extends ApiRouteName>(options: ApiOptions<TRoute> = {}) => apiClients[options.client || 'default']

export const isRequestCanceled = (error: unknown): boolean => (
    axios.isCancel(error)
    || (
        axios.isAxiosError(error)
        && (
            error.code === 'ERR_CANCELED'
            || error.message === 'canceled'
            || error.message === 'Request aborted'
        )
    )
)

export const apiGet = <TRoute extends ApiRouteName>(
    name: TRoute,
    options: ApiOptions<TRoute> = {},
): Promise<ApiRouteResponse<TRoute>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).get<ApiRouteResponse<TRoute>>(endpoint.url, buildRequestConfig(name, options))
        .then((response) => response.data)
}

export const apiPost = <TRoute extends ApiRouteName>(
    name: TRoute,
    body?: ApiRouteBody<TRoute>,
    options: ApiOptions<TRoute> = {},
): Promise<ApiRouteResponse<TRoute>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).post<ApiRouteResponse<TRoute>>(endpoint.url, body, buildRequestConfig(name, options))
        .then((response) => response.data)
}

export const apiPut = <TRoute extends ApiRouteName>(
    name: TRoute,
    body?: ApiRouteBody<TRoute>,
    options: ApiOptions<TRoute> = {},
): Promise<ApiRouteResponse<TRoute>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).put<ApiRouteResponse<TRoute>>(endpoint.url, body, buildRequestConfig(name, options))
        .then((response) => response.data)
}

export const apiDelete = <TRoute extends ApiRouteName>(
    name: TRoute,
    options: ApiOptions<TRoute> = {},
): Promise<ApiRouteResponse<TRoute>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).delete<ApiRouteResponse<TRoute>>(endpoint.url, buildRequestConfig(name, options))
        .then((response) => response.data)
}
